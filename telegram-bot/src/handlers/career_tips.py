from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from src.handlers.helpers import safe_callback_answer, safe_edit_message
from src.keyboards.inline import create_back_to_main_keyboard
from src.services.container import ServiceContainer
from src.utils.callback_factories import MainMenuActions, MainMenuCallback
from src.utils.i18n import gettext as _

router = Router(name="career_tips")


@router.callback_query(MainMenuCallback.filter(F.action == MainMenuActions.CAREER_TIPS))
async def career_tips(
    callback: CallbackQuery,
    services: ServiceContainer,
    state: FSMContext,
    user_lang: str | None = None,
) -> None:
    """Placeholder for career tips feature."""
    await safe_callback_answer(callback)
    keyboard = create_back_to_main_keyboard(user_lang)
    await safe_edit_message(callback.message, _("service_unavailable", locale=user_lang), reply_markup=keyboard)
