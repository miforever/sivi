from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from src.handlers.helpers import safe_callback_answer, safe_edit_message
from src.keyboards.inline import create_back_to_main_keyboard
from src.services.container import ServiceContainer
from src.utils.callback_factories import MainMenuActions, MainMenuCallback
from src.utils.i18n import gettext as _

router = Router(name="interview_practice")


@router.callback_query(MainMenuCallback.filter(F.action == MainMenuActions.INTERVIEW_PRACTICE))
async def interview_practice(
    callback: CallbackQuery,
    services: ServiceContainer,
    state: FSMContext,
    user_lang: str | None = None,
) -> None:
    """Placeholder for interview practice feature."""
    await safe_callback_answer(callback)
    keyboard = create_back_to_main_keyboard(user_lang)
    await safe_edit_message(callback.message, _("service_unavailable", locale=user_lang), reply_markup=keyboard)
