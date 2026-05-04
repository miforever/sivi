"""Q&A question asking and answer handling."""

import asyncio
import logging

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove

from src.handlers.filters import PrivateChatOnlyFilter
from src.handlers.helpers import _go_main_menu
from src.keyboards.reply import create_cancel_keyboard, create_skip_keyboard
from src.services.container import ServiceContainer
from src.utils.i18n import gettext as _
from src.utils.validators import validate_email, validate_full_name, validate_phone

from ..helpers import handle_cancel_action
from ..states import ResumeState

logger = logging.getLogger(__name__)
router = Router(name="resume_qa_questions")


async def ask_question(
    message: Message,
    state: FSMContext,
    services: ServiceContainer,
    user_lang: str | None = None,
) -> None:
    """Ask current question to user."""
    try:
        data = await state.get_data()
        questions = data["questions"]
        current_index = data["current_question_index"]

        if current_index >= len(questions):
            await state.set_state(ResumeState.UPLOAD_PHOTO)
            skip_kb = create_skip_keyboard(user_lang)
            await message.answer(_("upload_photo", locale=user_lang), reply_markup=skip_kb)
            return

        question = questions[current_index]
        nav_row = []

        # On first question show Back (to position) + Cancel
        if current_index == 0:
            nav_row.append(KeyboardButton(text=_("back", locale=user_lang)))
        else:
            nav_row.append(KeyboardButton(text=_("previous_question", locale=user_lang)))

        nav_row.append(KeyboardButton(text=_("cancel_button", locale=user_lang)))

        rows = [nav_row]

        # Optional questions get a Skip button on its own row above nav.
        if not question.get("is_required", True):
            rows.insert(0, [KeyboardButton(text=_("skip_button", locale=user_lang))])

        keyboard = ReplyKeyboardMarkup(
            keyboard=rows,
            resize_keyboard=True,
            one_time_keyboard=True,
            selective=True,
        )

        await message.answer(question["text"], reply_markup=keyboard)
        await state.set_state(ResumeState.WAITING_FOR_ANSWER)

    except Exception as e:
        logger.error("Error asking question: %s", str(e))
        await message.answer(_("error_occurred_retry", locale=user_lang))


@router.message(PrivateChatOnlyFilter(), ResumeState.ASK_POSITION)
async def handle_position_input_qa(
    message: Message,
    state: FSMContext,
    services: ServiceContainer,
    user_lang: str | None = None,
) -> None:
    """Handle position input for QA flow, fetch questions from backend."""
    try:
        if message.text == _("cancel_button", locale=user_lang):
            await handle_cancel_action(message, state, services, message.from_user.id, user_lang)
            return

        position = message.text.strip()
        if len(position) < 2:
            await message.answer(_("invalid_position", locale=user_lang))
            return

        questions = await services.backend.get_questions(user_lang, position)
        if not questions:
            await message.answer(_("failed_to_load_questions", locale=user_lang), reply_markup=ReplyKeyboardRemove())
            await state.clear()
            await asyncio.sleep(1)
            await _go_main_menu(message.from_user.id, message, state, services, user_lang, send_new=True)
            return

        await state.update_data(
            position=position,
            current_question_index=0,
            questions=questions,
            answers={},
        )

        await ask_question(message, state, services, user_lang)

    except Exception as e:
        logger.error("Error handling QA position input: %s", str(e))
        await message.answer(_("error_occurred_later", locale=user_lang))
        await state.clear()


@router.message(PrivateChatOnlyFilter(), ResumeState.WAITING_FOR_ANSWER)
async def handle_answer(
    message: Message,
    state: FSMContext,
    services: ServiceContainer,
    user_lang: str | None = None,
) -> None:
    """Handle user answer to question."""
    try:
        if message.text == _("cancel_button", locale=user_lang):
            await handle_cancel_action(message, state, services, message.from_user.id, user_lang)
            return

        # Back from first question -> ask for position again
        if message.text == _("back", locale=user_lang):
            await message.answer(_("ask_position", locale=user_lang), reply_markup=create_cancel_keyboard(user_lang))
            await state.set_state(ResumeState.ASK_POSITION)
            return

        if message.text == _("previous_question", locale=user_lang):
            data = await state.get_data()
            current_index = data["current_question_index"]
            if current_index > 0:
                await state.update_data(current_question_index=current_index - 1)
            await ask_question(message, state, services, user_lang)
            return

        data = await state.get_data()
        current_index = data["current_question_index"]
        questions = data.get("questions", [])
        answers = data.get("answers", {})

        q = questions[current_index]
        field_name = q.get("field_name", "")
        is_required = q.get("is_required", True)
        text = (message.text or "").strip()

        # Skip button: only rendered for optional questions. Advance without
        # recording an answer so the finalizer simply omits that field.
        if not is_required and text == _("skip_button", locale=user_lang):
            await state.update_data(current_question_index=current_index + 1)
            await ask_question(message, state, services, user_lang)
            return

        # Per-field validation. Required fields (full_name, email) are strict.
        # Phone is optional in the question set but has no skip button, so we
        # only reject when the user clearly attempted a phone number (digits
        # present) and it does not parse — otherwise a free-form answer like
        # "don't have one" is allowed through for the LLM to interpret.
        if field_name == "full_name" and not validate_full_name(text):
            await message.answer(_("invalid_full_name", locale=user_lang))
            return
        if field_name == "email" and not validate_email(text):
            await message.answer(_("invalid_email", locale=user_lang))
            return
        if field_name == "phone" and any(c.isdigit() for c in text) and not validate_phone(text):
            await message.answer(_("invalid_phone", locale=user_lang))
            return

        answers[current_index] = {
            "category": q.get("category", ""),
            "field_name": field_name,
            "text": text,
        }

        await state.update_data(
            answers=answers,
            current_question_index=current_index + 1,
        )
        await ask_question(message, state, services, user_lang)

    except Exception as e:
        logger.error("Error handling answer: %s", str(e))
        await message.answer(_("error_occurred_retry", locale=user_lang))
