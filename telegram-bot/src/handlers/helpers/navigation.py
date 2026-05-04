import logging
import random

from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.handlers.helpers.message import dismiss_reply_keyboard, safe_edit_message
from src.keyboards.inline import create_main_menu_keyboard
from src.services.container import ServiceContainer
from src.utils.i18n import gettext as _

logger = logging.getLogger(__name__)


async def _go_main_menu(
    user_id: int,
    message: Message,
    state: FSMContext,
    services: ServiceContainer,
    user_lang: str | None,
    send_new: bool = False,
    welcome_msg: bool = False,
) -> None:
    """Internal logic for handling go main menu."""

    await state.clear()

    user_data = await services.user_service.get_user(user_id)
    user_name = user_data.get("user_name")

    if welcome_msg:
        message_text = _("welcome", locale=user_lang, user_name=user_name)
    else:
        body_messages = _("main_menu_messages", locale=user_lang, user_name=user_name).split("|")
        body_message = random.choice(body_messages)
        message_text = body_message

    # Temporarily hide Pro badge for everyone
    keyboard = create_main_menu_keyboard(user_lang, has_subscription=False)

    if send_new:
        await dismiss_reply_keyboard(message, "🏠")
        await message.answer(message_text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await safe_edit_message(message, message_text, reply_markup=keyboard, parse_mode="HTML")
