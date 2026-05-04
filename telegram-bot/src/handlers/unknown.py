"""Unknown command handler for the bot."""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.handlers.filters import PrivateChatOnlyFilter
from src.handlers.helpers import _go_main_menu
from src.keyboards.inline import create_language_keyboard
from src.services.container import ServiceContainer
from src.utils.i18n import gettext as _

router = Router(name="unknown")


@router.message(PrivateChatOnlyFilter(), F.text.startswith("/"))
async def handle_unknown_command(message: Message, services: ServiceContainer, user_lang: str | None) -> None:
    """
    Handle any unrecognized commands or messages.

    This is a fallback handler that catches all messages that don't match
    any other handlers and provides helpful guidance to the user.
    """
    user = await services.user_service.get_user(message.from_user.id)

    if not user:
        await message.answer(
            _("select_language", locale="uz"), reply_markup=create_language_keyboard(is_registered=False)
        )
        return

    # Extract the command from the message
    command = message.text.split()[0]  # Get the first word (the command)
    await message.answer(_("unknown_command", locale=user_lang, command=command), parse_mode="HTML")


@router.message(PrivateChatOnlyFilter(), F.text)
async def handle_unknown_message(
    message: Message,
    state: FSMContext,
    user_lang: str | None,
    services: ServiceContainer,
) -> None:
    """
    Handle any unrecognized text messages (non-commands).

    Unrecognized reply-button presses typically mean the user is in a stale
    state (e.g. job feed after cache clear) where the expected handler is no
    longer registered. Silently redirect them to the main menu instead of
    showing an "option not found" error.
    """
    user = await services.user_service.get_user(message.from_user.id)

    if not user:
        await message.answer(
            _("select_language", locale="uz"), reply_markup=create_language_keyboard(is_registered=False)
        )
        return

    await _go_main_menu(
        message.from_user.id,
        message,
        state,
        services,
        user_lang,
        send_new=True,
    )
