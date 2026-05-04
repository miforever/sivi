import logging

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.config import get_settings
from src.handlers.helpers import safe_callback_answer, safe_edit_message
from src.keyboards.inline import create_back_to_main_keyboard
from src.services.container import ServiceContainer
from src.services.states import FeedbackStates
from src.utils.callback_factories import MainMenuActions, MainMenuCallback
from src.utils.i18n import gettext as _

logger = logging.getLogger(__name__)

router = Router(name="feedback")


@router.callback_query(MainMenuCallback.filter(F.action == MainMenuActions.FEEDBACK))
async def feedback_start(
    callback: CallbackQuery,
    services: ServiceContainer,
    state: FSMContext,
    user_lang: str | None = None,
) -> None:
    """Prompt user to write feedback."""
    await safe_callback_answer(callback)
    await state.set_state(FeedbackStates.WAITING_FEEDBACK)
    keyboard = create_back_to_main_keyboard(user_lang)
    await safe_edit_message(
        callback.message,
        _("feedback_prompt", locale=user_lang),
        reply_markup=keyboard,
    )


@router.message(FeedbackStates.WAITING_FEEDBACK)
async def feedback_received(
    message: Message,
    services: ServiceContainer,
    state: FSMContext,
    user_lang: str | None = None,
) -> None:
    """Forward user feedback to all admins."""
    await state.clear()

    feedback_text = message.text
    if not feedback_text:
        keyboard = create_back_to_main_keyboard(user_lang)
        await message.answer(
            _("feedback_empty", locale=user_lang),
            reply_markup=keyboard,
        )
        return

    user = message.from_user
    user_name = user.full_name or ""
    username = f"@{user.username}" if user.username else _("feedback_no_username", locale=user_lang)

    admin_message = (
        f"📬 <b>{_('feedback_new', locale='en')}</b>\n\n"
        f"<b>From:</b> {user_name} ({username})\n"
        f"<b>User ID:</b> <code>{user.id}</code>\n\n"
        f"<b>Message:</b>\n{feedback_text}"
    )

    settings = get_settings()
    bot: Bot = message.bot
    for admin_id in settings.ADMIN_IDS:
        try:
            await bot.send_message(admin_id, admin_message)
        except Exception:
            logger.warning("Failed to send feedback to admin %s", admin_id)

    keyboard = create_back_to_main_keyboard(user_lang)
    await message.answer(
        _("feedback_thanks", locale=user_lang),
        reply_markup=keyboard,
    )
