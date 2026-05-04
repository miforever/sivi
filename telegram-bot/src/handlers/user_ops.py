"""Register handlers for the bot."""

import logging
import re

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.handlers.filters import PrivateChatOnlyFilter
from src.handlers.helpers import _go_main_menu
from src.services.container import ServiceContainer
from src.services.states import UserUpdateStates
from src.utils.i18n import gettext as _

logger = logging.getLogger(__name__)
router = Router(name="register")


def is_valid_user_name(name: str) -> bool:
    """
    Validate user name or nickname allowing Latin, Cyrillic, and other Unicode letters.

    Rules:
    - Must be at least 2 characters long
    - Must contain only letters (any script), numbers, spaces, hyphens, underscores, and apostrophes
    - Must contain at least one letter
    - Maximum length of 20 characters
    """
    if not name or len(name.strip()) < 2:
        return False

    if len(name.strip()) > 20:
        return False

    # Allow Unicode letters, numbers, spaces, hyphens, underscores, and apostrophes
    # Using \w which includes letters and numbers in Unicode mode
    # Plus explicitly allowing spaces, hyphens, underscores, and apostrophes
    pattern = r"^[\w\s\-']+$"

    if not re.match(pattern, name.strip(), re.UNICODE):
        return False

    # Check that it contains at least one letter (not just numbers and special characters)
    # \w includes letters, so we check if there's at least one non-digit, non-underscore character
    if not any(c.isalpha() for c in name.strip()):
        return False

    return True


@router.message(UserUpdateStates.ASK_USER_NAME, PrivateChatOnlyFilter())
async def register_user(
    message: Message,
    services: ServiceContainer,
    state: FSMContext,
) -> None:

    data = await state.get_data()
    lang_code = data.get("lang_code")

    user_name = message.text.strip()

    if not is_valid_user_name(user_name):
        await message.answer(_("invalid_user_name", locale=lang_code))
        return

    user_name = user_name.split()[0].capitalize()

    user_data = {
        "telegram_id": message.from_user.id,
        "first_name": message.from_user.first_name or "",
        "last_name": message.from_user.last_name or "",
        "user_name": user_name,
        "username": message.from_user.username or "",
        "language": lang_code,
    }
    await services.user_service.create_user(user_data)

    await _go_main_menu(message.from_user.id, message, state, services, lang_code, send_new=True, welcome_msg=True)


@router.message(UserUpdateStates.UPDATE_USER_NAME, PrivateChatOnlyFilter())
async def update_user_name(message: Message, services: ServiceContainer, state: FSMContext, user_lang: str) -> None:

    user_name = message.text.strip()

    if not is_valid_user_name(user_name):
        await message.answer(_("invalid_user_name", locale=user_lang))
        return

    user_name = user_name.split()[0].capitalize()

    user_data = {"user_name": user_name}
    await services.user_service.update_user(message.from_user.id, user_data)

    await _go_main_menu(message.from_user.id, message, state, services, user_lang, send_new=True, welcome_msg=True)
