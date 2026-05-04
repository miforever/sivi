"""Start Q&A resume creation and language selection."""

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, KeyboardButton, ReplyKeyboardMarkup

from src.config import get_settings
from src.handlers.helpers import safe_callback_answer, safe_edit_message
from src.keyboards.inline import create_back_to_main_keyboard, create_language_keyboard_for_resume
from src.services.container import ServiceContainer
from src.utils.callback_factories import LanguageCallback, MainMenuActions, MainMenuCallback
from src.utils.i18n import LANGUAGES
from src.utils.i18n import gettext as _

from ..states import ResumeState

logger = logging.getLogger(__name__)
router = Router(name="resume_qa_start")

settings = get_settings()


@router.callback_query(MainMenuCallback.filter(F.action == MainMenuActions.CREATE_NEW))
async def start_qa_creation(
    callback: CallbackQuery,
    services: ServiceContainer,
    state: FSMContext,
    user_lang: str | None = None,
) -> None:
    """Start Q&A based resume creation."""
    await safe_callback_answer(callback)
    await state.clear()

    try:
        # Temporarily free for all users (no subscription or credit check)
        user_resumes = await services.resume_service.get_user_resumes(callback.from_user.id)
        if user_resumes and len(user_resumes) >= settings.MAX_RESUME_SLOTS:
            await safe_edit_message(
                callback.message,
                _("resume_limit_reached", locale=user_lang, resume_limit=settings.MAX_RESUME_SLOTS),
                reply_markup=create_back_to_main_keyboard(user_lang),
            )
            return

        language_keyboard = create_language_keyboard_for_resume(user_lang)

        info_message = _("resume_language_info", locale=user_lang)

        await callback.message.edit_text(
            info_message,
            reply_markup=language_keyboard,
            parse_mode="HTML",
        )
        await state.set_state(ResumeState.SELECT_RESUME_LANGUAGE)

    except Exception as e:
        logger.error("Error starting QA creation: %s", str(e))
        await callback.message.answer(_("error_occurred_later", locale=user_lang))
        await state.clear()


@router.callback_query(ResumeState.SELECT_RESUME_LANGUAGE, LanguageCallback.filter())
async def handle_language_selection(
    callback: CallbackQuery,
    callback_data: LanguageCallback,
    state: FSMContext,
    services: ServiceContainer,
    user_lang: str | None = None,
) -> None:
    """Handle resume language selection."""
    await safe_callback_answer(callback)

    try:
        resume_lang = callback_data.lang_code

        if resume_lang not in LANGUAGES:
            await callback.answer(_("invalid_language", locale=user_lang))
            return

        # Store selected resume language and ask for desired position
        await state.update_data(resume_language=resume_lang)

        language_name = LANGUAGES[resume_lang]["name"]
        confirmation = _("resume_language_selected", locale=user_lang, language_name=language_name)
        await safe_edit_message(callback.message, confirmation, parse_mode="HTML", reply_markup=None)

        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=_("cancel_button", locale=user_lang))]],
            resize_keyboard=True,
            one_time_keyboard=True,
            selective=True,
        )
        await callback.message.answer(_("ask_position", locale=user_lang), reply_markup=keyboard)
        await state.set_state(ResumeState.ASK_POSITION)

    except Exception as e:
        logger.error("Error handling language selection: %s", str(e))
        await callback.message.answer(_("error_occurred_later", locale=user_lang))
        await state.clear()
