"""Language-related handlers for the bot."""

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.handlers.filters import PrivateChatOnlyFilter
from src.handlers.helpers import _go_main_menu, dismiss_reply_keyboard, safe_edit_message
from src.keyboards.inline import create_language_keyboard
from src.services.container import ServiceContainer
from src.services.states import MainMenuState, UserUpdateStates
from src.utils.callback_factories import LanguageCallback
from src.utils.i18n import LANGUAGES
from src.utils.i18n import gettext as _

logger = logging.getLogger(__name__)
router = Router(name="language")


@router.message(PrivateChatOnlyFilter(), Command(commands=["language", "lang", "l", "til"]))
async def handle_language_command(
    message: Message,
    services: ServiceContainer,
    state: FSMContext,
) -> None:
    """Handle /language command."""
    user = await services.user_service.get_user(message.from_user.id)
    is_registered = bool(user)

    if is_registered:
        await dismiss_reply_keyboard(message, "🌐")

    await message.answer(
        _("select_language", locale="uz"), reply_markup=create_language_keyboard(is_registered=is_registered)
    )

    await state.set_state(MainMenuState.LANGUAGE_SELECTION)


@router.callback_query(MainMenuState.LANGUAGE_SELECTION, LanguageCallback.filter())
async def handle_language_selection(
    callback: CallbackQuery,
    callback_data: LanguageCallback,
    services: ServiceContainer,
    state: FSMContext,
) -> None:
    """Handle language selection from inline keyboard.

    Posts language preference to backend API and stores in cache.
    """
    lang_code = callback_data.lang_code
    is_registered = callback_data.is_registered

    if lang_code not in LANGUAGES:
        await callback.answer(_("invalid_language", locale="en"))
        return

    if not is_registered:
        await safe_edit_message(callback.message, _("ask_user_name", locale=lang_code), reply_markup=None)
        await state.set_state(UserUpdateStates.ASK_USER_NAME)
        await state.update_data(lang_code=lang_code)
        return

    success = await services.user_service.update_user(
        telegram_id=callback.from_user.id, user_data={"language": lang_code}
    )

    if success:
        lang = LANGUAGES[lang_code]
        await callback.message.edit_text(_("language_set", locale=lang_code, language_name=lang["name"]))

        await _go_main_menu(callback.from_user.id, callback.message, state, services, lang_code, send_new=True)
    else:
        await callback.answer(_("error_setting_language", locale=lang_code))
