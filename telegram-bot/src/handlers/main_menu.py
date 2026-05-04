import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from src.handlers.helpers import _go_main_menu, safe_callback_answer
from src.services.container import ServiceContainer
from src.utils.callback_factories import MainMenuActions, MainMenuCallback
from src.utils.i18n import gettext as _

logger = logging.getLogger(__name__)
router = Router(name="resume")


@router.callback_query(MainMenuCallback.filter(F.action == MainMenuActions.GO_MAIN))
async def handle_go_main_menu(
    callback: CallbackQuery, services: ServiceContainer, state: FSMContext, user_lang: str | None = None
) -> None:
    """Go back to main menu."""
    await safe_callback_answer(callback)

    try:
        await _go_main_menu(callback.from_user.id, callback.message, state, services, user_lang)
    except TimeoutError:
        logger.error("Timeout in go main menu for user %s", callback.from_user.id)
        await callback.message.answer(_("error_occurred_general", locale=user_lang))
        await state.clear()
    except Exception as e:
        logger.error("Error in go main menu for user %s: %s", callback.from_user.id, str(e))
        await callback.message.answer(_("error_occurred_general", locale=user_lang))
        await state.clear()
