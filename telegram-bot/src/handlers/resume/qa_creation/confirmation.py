"""Resume confirmation and cancellation handlers."""

import asyncio
import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from src.handlers.helpers import (
    _go_main_menu,
    animate_dots,
    safe_callback_answer,
    safe_edit_message,
    safe_edit_reply_markup,
)
from src.keyboards.reply import create_resume_confirmation_keyboard
from src.services.backend.base import WeeklyLimitReachedError
from src.services.container import ServiceContainer
from src.utils.callback_factories import ResumeCreationCallback
from src.utils.i18n import gettext as _

from ..helpers import process_contact_fields, validate_resume_fields
from ..states import ResumeState
from .finalization import finalize_qa_resume

logger = logging.getLogger(__name__)
router = Router(name="resume_qa_confirmation")


async def show_confirmation(
    message: Message,
    state: FSMContext,
    user_lang: str | None = None,
) -> None:
    """Show resume preview and confirmation."""
    try:
        data = await state.get_data()
        questions = data["questions"]
        preview = _("resume_preview_title", locale=user_lang)

        max_line_chars = 120  # roughly 2 lines in Telegram

        for idx, answer_obj in data.get("answers", {}).items():
            question_text = questions[int(idx)]["text"] if str(idx).isdigit() else str(idx)
            answer_text = answer_obj.get("text") if isinstance(answer_obj, dict) else str(answer_obj)

            # Truncate answer to ~2 lines
            if len(answer_text) > max_line_chars:
                answer_text = answer_text[:max_line_chars] + "..."

            preview += f"<b>{int(idx) + 1 if str(idx).isdigit() else idx}.</b>\n"
            preview += f"<b>{_('question_label', locale=user_lang)}</b> {question_text}\n"
            preview += f"<b>{_('answer_label', locale=user_lang)}</b> {answer_text}\n\n"

        if "photo_file_id" in data:
            preview += _("includes_photo", locale=user_lang) + "\n\n"

        await message.answer(
            preview, reply_markup=create_resume_confirmation_keyboard(user_lang=user_lang), parse_mode="HTML"
        )
        await state.set_state(ResumeState.CONFIRM_RESUME)

    except Exception as e:
        logger.error("Error showing confirmation: %s", str(e))
        await message.answer(_("error_occurred_retry", locale=user_lang))


@router.message(ResumeState.CONFIRM_RESUME, F.text)
async def handle_confirmation(
    message: Message,
    state: FSMContext,
    services: ServiceContainer,
    user_lang: str | None = None,
) -> None:
    """Handle resume confirmation and generation."""
    await safe_edit_reply_markup(message, reply_markup=ReplyKeyboardRemove())

    try:
        data = await state.get_data()
        answers = data.get("answers", {})
        questions = data.get("questions", [])
        photo_file_id = data.get("photo_file_id")
        resume_language = data.get("resume_language")

        photo_bytes = None
        if photo_file_id:
            try:
                file = await message.bot.get_file(photo_file_id)
                photo_file_obj = await message.bot.download_file(file.file_path)
                photo_bytes = photo_file_obj.getvalue()
            except Exception as e:
                logger.error(f"Failed to download photo: {e}")

        personal_fields = {
            "full_name": "",
            "email": "",
            "phone": "",
            "location": "",
            "position": "",
        }

        qa_pairs = []
        for idx_str, answer_obj in answers.items():
            try:
                idx = int(idx_str)
            except Exception:
                idx = idx_str

            if isinstance(idx, int) and 0 <= idx < len(questions):
                q = questions[idx]
                field_name = q.get("field_name")
                answer_text = answer_obj.get("text") if isinstance(answer_obj, dict) else str(answer_obj)

                if field_name in personal_fields:
                    personal_fields[field_name] = answer_text

                qa_pairs.append(
                    {
                        "question": q.get("text", str(field_name) or str(idx)),
                        "answer": answer_text,
                    }
                )

        missing_required, missing_contact = await validate_resume_fields(personal_fields)

        # If position wasn't collected via Q&A (we asked it before), use stored position
        if not personal_fields.get("position"):
            personal_fields["position"] = data.get("position", "")

        if missing_required:
            missing_text = ", ".join(missing_required)
            await safe_edit_message(
                message,
                _("missing_required_fields", locale=user_lang, missing_fields=missing_text),
            )
            await state.clear()
            await asyncio.sleep(1)
            await _go_main_menu(message.from_user.id, message, state, services, user_lang, send_new=True)
            return

        base_text = _("generating_resume", locale=user_lang).rstrip(".")
        gen_msg = await message.answer(f"{base_text}.", reply_markup=ReplyKeyboardRemove())
        anim_task = asyncio.create_task(animate_dots(gen_msg, base_text))

        # Generate resume data from Q&A using backend
        user_info = {
            "full_name": personal_fields["full_name"],
            "email": personal_fields["email"],
            "phone": personal_fields["phone"],
            "location": personal_fields["location"],
            "position": personal_fields["position"],
        }

        try:
            resume_data, credits_remaining = await services.backend.generate_resume_from_qa(
                message.from_user.id,
                qa_pairs,
                user_info,
                language=resume_language,
            )
        except WeeklyLimitReachedError as e:
            anim_task.cancel()
            import re

            date_match = re.search(r"\d{2}\.\d{2}\.\d{4}", str(e))
            reset_date = date_match.group() if date_match else "—"
            await message.answer(
                _("weekly_ai_limit_reached", locale=user_lang, reset_date=reset_date),
                reply_markup=ReplyKeyboardRemove(),
            )
            await state.clear()
            await asyncio.sleep(1)
            await _go_main_menu(message.from_user.id, message, state, services, user_lang, send_new=True)
            return

        anim_task.cancel()

        if not resume_data:
            await safe_edit_message(gen_msg, _("ai_service_error", locale=user_lang))
            await state.clear()
            await asyncio.sleep(1)
            await _go_main_menu(message.from_user.id, message, state, services, user_lang, send_new=True)
            return

        if missing_contact:
            await safe_edit_message(gen_msg, _("missing_contact_methods", locale=user_lang))
            await state.update_data(
                qa_resume_data=resume_data,
                credits_remaining=credits_remaining,
                photo_bytes=photo_bytes,
                missing_contact_fields=missing_contact,
                from_qa_flow=True,
            )
            await process_contact_fields(message, state, missing_contact, resume_data, user_lang)
            return

        await finalize_qa_resume(
            message, state, services, resume_data, photo_bytes, resume_language, message.from_user.id, user_lang
        )

    except Exception as e:
        logger.error("Error confirming resume: %s", str(e))
        await message.answer(_("error_occurred_general", locale=user_lang))


@router.callback_query(ResumeState.CONFIRM_RESUME, ResumeCreationCallback.filter(F.action == "cancel"))
async def handle_cancellation(
    callback: CallbackQuery,
    state: FSMContext,
    services: ServiceContainer,
    user_lang: str | None = None,
) -> None:
    """Handle resume cancellation."""
    await safe_callback_answer(callback)
    try:
        await state.clear()
        await services.cache.clear_resume_answers(callback.from_user.id)
        await safe_edit_message(callback.message, _("resume_creation_cancelled", locale=user_lang), reply_markup=None)
    except Exception as e:
        logger.error("Error cancelling resume: %s", str(e))
        await callback.answer(_("error_occurred_general", locale=user_lang))
