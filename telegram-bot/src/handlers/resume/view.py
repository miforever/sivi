"""Resume viewing, downloading, and deletion handlers."""

import logging
from datetime import datetime

from aiogram import F, Router
from aiogram.types import BufferedInputFile, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from src.handlers.helpers import safe_callback_answer, safe_edit_message
from src.keyboards.inline import create_back_to_main_keyboard, create_delete_confirmation_keyboard
from src.services.container import ServiceContainer
from src.utils.callback_factories import MainMenuActions, MainMenuCallback, ResumeActions, ResumeCallback
from src.utils.i18n import gettext as _

logger = logging.getLogger(__name__)
router = Router(name="resume_view")


@router.callback_query(MainMenuCallback.filter(F.action == MainMenuActions.VIEW_DELETE))
async def view_resumes_list(
    callback: CallbackQuery, callback_data: MainMenuCallback, services: ServiceContainer, user_lang: str | None = None
) -> None:
    """Display list of user's resumes."""
    await safe_callback_answer(callback)
    delete_message = callback_data.delete

    if delete_message:
        await callback.message.delete()

    try:
        resumes = await services.cache.get_user_resumes(callback.from_user.id)
        if not resumes:
            resumes = await services.backend.get_user_resumes(callback.from_user.id)
            await services.cache.save_user_resumes(callback.from_user.id, resumes)

        if not resumes:
            keyboard = create_back_to_main_keyboard(user_lang)
            await safe_edit_message(callback.message, _("no_resumes", locale=user_lang), reply_markup=keyboard)
            return

        keyboard_buttons = []
        for resume in resumes:
            resume_title = resume.get("title", "").strip()
            resume_id = resume.get("id", "0")

            keyboard_buttons.append(
                [
                    InlineKeyboardButton(
                        text=resume_title or _("untitled_resume", locale=user_lang),
                        callback_data=ResumeCallback(action=ResumeActions.VIEW, resume_id=resume_id).pack(),
                    )
                ]
            )

        keyboard_buttons.append(
            [
                InlineKeyboardButton(
                    text=_("back", locale=user_lang),
                    callback_data=MainMenuCallback(action=MainMenuActions.GO_MAIN).pack(),
                )
            ]
        )

        await safe_edit_message(
            callback.message,
            _("your_resumes", locale=user_lang),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons),
            parse_mode="HTML",
        )

    except Exception as e:
        logger.error("Error viewing resumes: %s", str(e))
        await callback.answer(_("error_occurred_general", locale=user_lang))


@router.callback_query(ResumeCallback.filter(F.action == ResumeActions.VIEW))
async def view_single_resume(
    callback: CallbackQuery, callback_data: ResumeCallback, services: ServiceContainer, user_lang: str | None = None
) -> None:
    """Display a specific resume."""
    await safe_callback_answer(callback)

    try:
        await callback.message.delete()
        resume_id = callback_data.resume_id

        resume_file = await services.backend.export_resume_pdf(callback.from_user.id, resume_id)
        resume_data = await services.cache.get_user_resume(callback.from_user.id, resume_id)

        if not resume_data:
            user_resumes = await services.backend.get_user_resumes(callback.from_user.id)
            await services.cache.save_user_resumes(callback.from_user.id, user_resumes)
            resume_data = await services.cache.get_user_resume(callback.from_user.id, resume_id)

        if not resume_file or not resume_data:
            await safe_callback_answer(callback, _("resume_not_found", locale=user_lang))
            return

        pdf_input = BufferedInputFile(resume_file, filename="resume.pdf")
        created_at = resume_data.get("created_at", "")
        formatted_date = format_date(created_at, user_lang)

        caption = f"<b>{_('created_at', locale=user_lang)}</b>: {formatted_date}"

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=_("delete_button", locale=user_lang),
                        callback_data=ResumeCallback(action=ResumeActions.DELETE, resume_id=resume_id).pack(),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=_("back", locale=user_lang),
                        callback_data=MainMenuCallback(action=MainMenuActions.VIEW_DELETE, delete=True).pack(),
                    )
                ],
            ]
        )

        await callback.message.answer_document(pdf_input, caption=caption, reply_markup=keyboard)

    except Exception as e:
        logger.error("Error viewing resume: %s", str(e))
        await safe_callback_answer(callback, _("error_occurred_general", locale=user_lang))


@router.callback_query(ResumeCallback.filter(F.action == ResumeActions.DELETE))
async def confirm_delete_resume(
    callback: CallbackQuery, callback_data: ResumeCallback, services: ServiceContainer, user_lang: str | None = None
) -> None:
    """Show delete confirmation."""
    await safe_callback_answer(callback)
    await callback.message.delete()

    try:
        resume_id = callback_data.resume_id

        keyboard = create_delete_confirmation_keyboard(resume_id, user_lang)

        await callback.message.answer(
            _("confirm_delete_description", locale=user_lang), reply_markup=keyboard, parse_mode="HTML"
        )

    except Exception as e:
        logger.error("Error preparing delete: %s", str(e))
        await safe_callback_answer(callback, _("error_occurred_general", locale=user_lang))


@router.callback_query(ResumeCallback.filter(F.action == ResumeActions.CONFIRM_DELETE))
async def delete_resume(
    callback: CallbackQuery, callback_data: ResumeCallback, services: ServiceContainer, user_lang: str | None = None
) -> None:
    """Delete the resume."""
    await safe_callback_answer(callback)

    try:
        resume_id = callback_data.resume_id
        success = await services.backend.delete_resume(callback.from_user.id, resume_id)

        if success:
            user_resumes = await services.cache.get_user_resumes(callback.from_user.id)
            user_resumes = [r for r in user_resumes if r.get("id") != resume_id]
            await services.cache.save_user_resumes(callback.from_user.id, user_resumes)

            message_text = _("resume_deleted", locale=user_lang)
        else:
            message_text = _("failed_to_delete_resume", locale=user_lang)

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=_("back", locale=user_lang),
                        callback_data=MainMenuCallback(action=MainMenuActions.VIEW_DELETE).pack(),
                    )
                ]
            ]
        )

        await safe_edit_message(callback.message, message_text, reply_markup=keyboard)

    except Exception as e:
        logger.error("Error deleting resume: %s", str(e))
        await safe_callback_answer(callback, _("error_occurred_general", locale=user_lang))


def format_date(date_str: str, user_lang: str) -> str:
    """Format ISO date string to readable format in Uzbekistan time (GMT+5)."""
    try:
        if date_str and "T" in date_str:
            from zoneinfo import ZoneInfo

            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            uz_tz = ZoneInfo("Asia/Tashkent")
            dt = dt.astimezone(uz_tz)
            return dt.strftime("%d.%m.%Y %H:%M") + " (GMT+5)"
        return date_str or _("not_specified", locale=user_lang)
    except Exception:
        return date_str or _("not_specified", locale=user_lang)
