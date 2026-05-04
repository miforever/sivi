"""
Command handlers for the Sivi Telegram Bot.

This module contains all command handlers to ensure they are registered
before text handlers and don't get caught by FSM or text message handlers.
"""

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from src.handlers.filters import PrivateChatOnlyFilter
from src.handlers.helpers import _go_main_menu, dismiss_reply_keyboard
from src.keyboards.inline import (
    create_back_to_main_keyboard,
    create_language_keyboard,
)
from src.services.container import ServiceContainer
from src.services.states import MainMenuState, UserUpdateStates
from src.utils.callback_factories import MainMenuActions, MainMenuCallback, ResumeActions, ResumeCallback
from src.utils.i18n import gettext as _

logger = logging.getLogger(__name__)

router = Router()


@router.message(PrivateChatOnlyFilter(), Command(commands=["start"]))
async def handle_start_command(
    message: Message, state: FSMContext, services: ServiceContainer, user_lang: str | None = None
) -> None:
    """Handle /start command."""
    user = await services.user_service.get_user(message.from_user.id)

    if not user:
        await message.answer(
            _("select_language", locale="uz"), reply_markup=create_language_keyboard(is_registered=False)
        )
        await state.set_state(MainMenuState.LANGUAGE_SELECTION)
        return

    await _go_main_menu(message.from_user.id, message, state, services, user_lang, send_new=True)


@router.message(PrivateChatOnlyFilter(), Command(commands=["help", "h", "yordam"]))
async def handle_help_command(
    message: Message, services: ServiceContainer, state: FSMContext, user_lang: str | None = None
) -> None:
    """Handle /help command."""
    user = await services.user_service.get_user(message.from_user.id)

    if not user:
        await message.answer(_("ask_user_name", locale=user_lang or "uz"))
        await state.set_state(UserUpdateStates.ASK_USER_NAME)
        return

    await dismiss_reply_keyboard(message, "❓")
    keyboard = create_back_to_main_keyboard(user_lang)
    await message.answer(_("help_message", locale=user_lang), reply_markup=keyboard)


@router.message(PrivateChatOnlyFilter(), Command(commands=["resumes"]))
async def handle_resumes_command(
    message: Message, services: ServiceContainer, state: FSMContext, user_lang: str | None = None
) -> None:
    """Handle /resumes command."""
    user = await services.user_service.get_user(message.from_user.id)

    if not user:
        await message.answer(_("ask_user_name", locale=user_lang or "uz"))
        await state.set_state(UserUpdateStates.ASK_USER_NAME)
        return

    await dismiss_reply_keyboard(message, "📄")

    try:
        resumes = await services.cache.get_user_resumes(message.from_user.id)
        if not resumes:
            resumes = await services.backend.get_user_resumes(message.from_user.id)

        if not resumes:
            keyboard = create_back_to_main_keyboard(user_lang)
            await message.answer(_("no_resumes", locale=user_lang), reply_markup=keyboard)
            return

        keyboard_buttons = []

        for resume in resumes:
            position = resume.get("position", _("untitled_resume", locale=user_lang))
            resume_id = resume.get("id", 0)
            if position:
                resume_text = position
            elif resume_id:
                resume_text = str(resume_id)
            else:
                resume_text = _("untitled_resume", locale=user_lang)

            keyboard_buttons.append(
                [
                    InlineKeyboardButton(
                        text=resume_text,
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

        await message.answer(
            _("your_resumes", locale=user_lang), reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        )

    except Exception as e:
        logger.error("Error showing resumes for user %s: %s", message.from_user.id, str(e))
        await message.answer(_("error_occurred_general", locale=user_lang))


@router.message(PrivateChatOnlyFilter(), Command(commands=["name"]))
async def handle_user_name_change(
    message: Message, services: ServiceContainer, state: FSMContext, user_lang: str | None = None
) -> None:
    """Handle /name command."""
    user = await services.user_service.get_user(message.from_user.id)

    if not user:
        await message.answer(_("ask_user_name", locale=user_lang or "uz"))
        await state.set_state(UserUpdateStates.ASK_USER_NAME)
        return

    await dismiss_reply_keyboard(message, "✏️")
    await message.answer(_("ask_user_name", locale=user_lang))
    await state.set_state(UserUpdateStates.UPDATE_USER_NAME)


@router.callback_query(F.data == "back_to_main_menu")
async def handle_back_to_main_menu(
    callback: CallbackQuery, user_lang: str | None = None, state: FSMContext = None
) -> None:
    """
    Handle the back_to_main_menu callback.

    Returns the user to the main menu.
    """
    if state:
        await state.clear()
    await callback.message.edit_text(_("back_to_main_menu", locale=user_lang), reply_markup=None)
