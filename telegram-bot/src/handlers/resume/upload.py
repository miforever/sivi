"""Resume upload and processing handlers."""

import asyncio
import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove

from src.config import get_settings
from src.handlers.filters import PrivateChatOnlyFilter
from src.handlers.helpers import _go_main_menu, animate_dots, safe_callback_answer, safe_edit_message
from src.keyboards.inline import (
    create_back_to_main_keyboard,
    get_profile_image_keyboard,
    get_resume_confirmation_keyboard,
)
from src.services.backend.base import WeeklyLimitReachedError
from src.services.container import ServiceContainer
from src.utils.callback_factories import MainMenuActions, MainMenuCallback, UploadActions, UploadConfirmCallback
from src.utils.i18n import gettext as _

from .helpers import (
    handle_cancel_action,
    image_bytes_to_data_uri,
    process_contact_fields,
    validate_resume_fields,
)
from .states import ResumeState

logger = logging.getLogger(__name__)
router = Router(name="resume_upload")

settings = get_settings()


@router.callback_query(MainMenuCallback.filter(F.action == MainMenuActions.UPLOAD_EXISTING))
async def start_upload(
    callback: CallbackQuery, services: ServiceContainer, state: FSMContext, user_lang: str | None = None
) -> None:
    """Start resume upload flow."""
    await safe_callback_answer(callback)

    # Temporarily treat everyone as Pro (no subscription check)
    # subscription_status = await services.subscription_service.get_user_subscription(callback.from_user.id)
    # has_subscription = subscription_status.get("has_active_subscription", False)
    # if not has_subscription:
    #     await safe_edit_message(
    #         callback.message,
    #         _("pro_required", locale=user_lang),
    #         reply_markup=get_pro_keyboard(user_lang)
    #     )
    #     return

    user_resumes = await services.resume_service.get_user_resumes(callback.from_user.id)
    if user_resumes and len(user_resumes) >= 3:
        await safe_edit_message(
            callback.message,
            _("resume_limit_reached", locale=user_lang, resume_limit=3),
            reply_markup=None,
        )
        await _go_main_menu(callback.from_user.id, callback.message, state, services, user_lang, send_new=True)
        return

    try:
        await asyncio.wait_for(handle_upload_flow(callback, services, state, user_lang), timeout=25.0)
    except TimeoutError:
        logger.error("Timeout in upload for user %s", callback.from_user.id)
        await callback.message.answer(_("error_occurred_general", locale=user_lang))
        await state.clear()
    except Exception as e:
        logger.error("Error starting upload: %s", str(e))
        await callback.message.answer(_("error_occurred_later", locale=user_lang))
        await state.clear()


async def handle_upload_flow(
    callback: CallbackQuery, services: ServiceContainer, state: FSMContext, user_lang: str | None = None
) -> None:
    """Handle upload flow logic."""
    user_resumes = await services.resume_service.get_user_resumes(callback.from_user.id)
    if user_resumes and len(user_resumes) >= settings.MAX_RESUME_SLOTS:
        await safe_edit_message(callback.message, _("resume_limit_reached", locale=user_lang), reply_markup=None)
        await _go_main_menu(callback.from_user.id, callback.message, state, services, user_lang, send_new=True)
        return

    keyboard = create_back_to_main_keyboard(user_lang)
    msg = await safe_edit_message(
        callback.message, _("upload_existing_resume_prompt", locale=user_lang), reply_markup=keyboard
    )

    await state.update_data(message_id=msg.message_id)
    await state.set_state(ResumeState.UPLOAD_RESUME)


@router.message(PrivateChatOnlyFilter(), ResumeState.UPLOAD_RESUME, F.document)
async def handle_document_upload(message: Message, state: FSMContext, user_lang: str | None = None) -> None:
    """Handle resume document upload."""
    try:
        # Validate file type
        resume = message.document
        mime_type = getattr(resume, "mime_type", "")
        file_name = getattr(resume, "file_name", "")

        # Allowed MIME types and extensions
        allowed_mime_types = [
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # docx
            "application/msword",  # doc
        ]
        allowed_extensions = [".pdf", ".docx", ".doc"]

        # Check MIME type or file extension
        is_valid_mime = mime_type in allowed_mime_types
        is_valid_extension = any(file_name.lower().endswith(ext) for ext in allowed_extensions)

        if not (is_valid_mime or is_valid_extension):
            await message.answer(
                _("invalid_file_type", locale=user_lang), reply_markup=create_back_to_main_keyboard(user_lang)
            )
            return

        # Check file size (optional - e.g., max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB in bytes
        if resume.file_size and resume.file_size > max_size:
            await message.answer(
                _("file_too_large", locale=user_lang), reply_markup=create_back_to_main_keyboard(user_lang)
            )
            return

        # Remove inline keyboard from the prompt message
        data = await state.get_data()
        message_id = data.get("message_id")

        if message_id:
            try:
                await message.bot.edit_message_reply_markup(
                    chat_id=message.chat.id, message_id=message_id, reply_markup=None
                )
            except Exception as e:
                logger.warning("Failed to remove keyboard from prompt message %s: %s", message_id, str(e))

        # Store resume data
        await state.update_data(
            resume_file_id=resume.file_id,
            resume_mime_type=mime_type,
            resume_file_name=file_name,
        )
        await state.set_state(ResumeState.UPLOAD_PROFILE_PHOTO)

        keyboard = get_profile_image_keyboard(user_lang)
        msg = await message.answer(_("profile_photo_prompt", locale=user_lang), reply_markup=keyboard)

        await state.update_data(message_id=msg.message_id)

    except Exception as e:
        logger.error("Error handling document: %s", str(e), exc_info=True)
        await message.answer(_("error_occurred_general", locale=user_lang))


@router.callback_query(F.data == "profile_photo_skip", ResumeState.UPLOAD_PROFILE_PHOTO)
async def skip_profile_photo(callback: CallbackQuery, state: FSMContext, user_lang: str | None = None) -> None:
    """Handle skipping profile photo upload."""
    await safe_callback_answer(callback)
    await state.update_data(photo_bytes=None)

    keyboard = get_resume_confirmation_keyboard(user_lang)
    await safe_edit_message(
        callback.message, _("confirm_uploaded_resume_prompt", locale=user_lang), reply_markup=keyboard
    )


@router.message(PrivateChatOnlyFilter(), ResumeState.UPLOAD_PROFILE_PHOTO)
async def handle_profile_photo(message: Message, state: FSMContext, user_lang: str | None = None) -> None:
    """Handle profile photo upload or skip."""

    keyboard = get_resume_confirmation_keyboard(user_lang)

    if message.photo:
        try:
            photo = message.photo[-1]
            file = await message.bot.get_file(photo.file_id)
            photo_file_obj = await message.bot.download_file(file.file_path)
            photo_bytes = photo_file_obj.getvalue()

            await state.update_data(photo_bytes=photo_bytes)
            await message.answer(_("profile_photo_uploaded", locale=user_lang), reply_markup=ReplyKeyboardRemove())

        except Exception as e:
            logger.error("Error processing photo: %s", str(e))
            await message.answer(_("error_processing_photo", locale=user_lang))

        data = await state.get_data()
        message_id = data.get("message_id")

        await message.bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=message_id, reply_markup=None)

        await message.answer(_("confirm_uploaded_resume_prompt", locale=user_lang), reply_markup=keyboard)
    else:
        await message.answer(_("upload_photo", locale=user_lang))


@router.callback_query(UploadConfirmCallback.filter())
async def handle_upload_confirmation(
    callback: CallbackQuery,
    callback_data: UploadConfirmCallback,
    state: FSMContext,
    services: ServiceContainer,
    user_lang: str | None = None,
) -> None:
    """Handle confirmation of uploaded resume."""
    action = callback_data.action
    if action == UploadActions.CANCEL:
        await _go_main_menu(callback.from_user.id, callback.message, state, services, user_lang)
        return

    try:
        data = await state.get_data()
        await safe_edit_message(callback.message, _("downloading_resume", locale=user_lang), reply_markup=None)

        resume_file_id = data.get("resume_file_id")
        file = await callback.bot.get_file(resume_file_id)
        file_obj = await callback.bot.download_file(file.file_path)
        file_bytes = file_obj.getvalue()

        mime_type = data.get("resume_mime_type")
        if isinstance(mime_type, str) and "/" in mime_type:
            file_type = mime_type.split("/")[-1].lower()
        else:
            name = data.get("resume_file_name") or ""
            file_type = name.rsplit(".", 1)[-1].lower() if "." in name else "pdf"

        base_text = _("processing_resume", locale=user_lang).rstrip(".")
        status_msg = await safe_edit_message(callback.message, f"{base_text}.")
        anim_task = asyncio.create_task(animate_dots(status_msg, base_text))

        try:
            resume_data, _credits_remaining = await services.backend.extract_resume(
                callback.from_user.id, file_bytes, file_type
            )
        except WeeklyLimitReachedError as e:
            anim_task.cancel()
            import re

            date_match = re.search(r"\d{2}\.\d{2}\.\d{4}", str(e))
            reset_date = date_match.group() if date_match else "—"
            await safe_edit_message(status_msg, _("weekly_ai_limit_reached", locale=user_lang, reset_date=reset_date))
            await asyncio.sleep(1)
            await _go_main_menu(callback.from_user.id, callback.message, state, services, user_lang)
            return

        anim_task.cancel()

        if not resume_data:
            await safe_edit_message(status_msg, _("ai_service_error", locale=user_lang))
            await asyncio.sleep(1)
            await _go_main_menu(callback.from_user.id, callback.message, state, services, user_lang)
            return

        missing_required, missing_contact = await validate_resume_fields(resume_data)

        if missing_required:
            missing_text = ", ".join(missing_required)
            await safe_edit_message(
                status_msg, _("missing_required_fields", locale=user_lang, missing_fields=missing_text)
            )
            await asyncio.sleep(1)
            await _go_main_menu(callback.from_user.id, callback.message, state, services, user_lang)
            return

        # Store the status message so finalize_uploaded_resume can edit it
        await state.update_data(status_message_id=status_msg.message_id)

        if missing_contact:
            await safe_edit_message(status_msg, _("missing_contact_methods", locale=user_lang))
            await state.update_data(parsed_resume_data=resume_data, missing_contact_fields=missing_contact)
            await process_contact_fields(callback.message, state, missing_contact, resume_data, user_lang)
            return

        if not resume_data.get("position", "").strip():
            await safe_edit_message(status_msg, _("position_missing_from_resume", locale=user_lang))
            await state.update_data(parsed_resume_data=resume_data)
            keyboard = ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text=_("cancel_button", locale=user_lang))]],
                resize_keyboard=True,
                one_time_keyboard=True,
                selective=True,
            )
            await callback.message.answer(_("please_provide_position", locale=user_lang), reply_markup=keyboard)
            await state.set_state(ResumeState.ASK_POSITION)
            return

        await finalize_uploaded_resume(status_msg, state, services, callback.from_user.id, user_lang, resume_data)

    except Exception as e:
        logger.error("Error confirming upload: %s", str(e))
        await callback.answer(_("error_occurred_general", locale=user_lang))


@router.message(PrivateChatOnlyFilter(), ResumeState.ASK_POSITION)
async def handle_position_input(
    message: Message, state: FSMContext, services: ServiceContainer, user_lang: str | None = None
) -> None:
    """Handle position input."""
    try:
        if message.text == _("cancel_button", locale=user_lang):
            await handle_cancel_action(message, state, services, message.from_user.id, user_lang)
            return

        position = message.text.strip()
        if len(position) < 2:
            await message.answer(_("invalid_position", locale=user_lang))
            return

        data = await state.get_data()
        resume_data = data.get("parsed_resume_data", {})

        resume_data["position"] = position
        await finalize_uploaded_resume(message, state, services, message.from_user.id, user_lang, resume_data)

    except Exception as e:
        logger.error("Error handling position: %s", str(e))
        await message.answer(_("error_occurred_general", locale=user_lang))
        await state.clear()


async def finalize_uploaded_resume(
    message: Message,
    state: FSMContext,
    services: ServiceContainer,
    user_id: int,
    user_lang: str,
    resume_data: dict | None = None,
) -> None:
    """Finalize uploaded resume."""
    data = await state.get_data()

    # Try to edit the original status message from the extraction step;
    # fall back to the message passed in if not available.
    status_message_id = data.get("status_message_id")
    if status_message_id:
        try:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=status_message_id,
                text=_("saving_resume", locale=user_lang),
            )
        except Exception:
            status_message_id = None

    try:
        if resume_data is None:
            resume_data = data.get("parsed_resume_data", {})

        photo_bytes = data.get("photo_bytes")
        profile_image = None
        if photo_bytes:
            profile_image = image_bytes_to_data_uri(photo_bytes)

        resume_data["origin"] = "uploaded"
        resume_data["profile_image"] = profile_image

        if not status_message_id:
            await safe_edit_message(message, _("saving_resume", locale=user_lang))

        saved_resume = await services.resume_service.save_resume(user_id, resume_data)

        if not saved_resume:
            if status_message_id:
                try:
                    await message.bot.edit_message_text(
                        chat_id=message.chat.id,
                        message_id=status_message_id,
                        text=_("backend_service_error", locale=user_lang),
                    )
                except Exception:
                    await message.answer(_("backend_service_error", locale=user_lang))
            else:
                await safe_edit_message(message, _("backend_service_error", locale=user_lang))
            await asyncio.sleep(1)
            await _go_main_menu(user_id, message, state, services, user_lang, send_new=True)
            await state.clear()
            return

        if status_message_id:
            try:
                await message.bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=status_message_id,
                    text=_("resume_upload_success", locale=user_lang),
                )
            except Exception:
                await message.answer(_("resume_upload_success", locale=user_lang))
        else:
            await safe_edit_message(message, _("resume_upload_success", locale=user_lang))
        await _go_main_menu(user_id, message, state, services, user_lang, send_new=True)

        await state.clear()

    except Exception as e:
        logger.error("Error finalizing upload: %s", str(e))
        if "RESUME_LIMIT_REACHED" in str(e):
            await message.answer(_("resume_limit_reached", locale=user_lang))
        else:
            await message.answer(_("backend_service_error", locale=user_lang))
        await asyncio.sleep(1)
        await _go_main_menu(message.from_user.id, message, state, services, user_lang, send_new=True)
        await state.clear()
