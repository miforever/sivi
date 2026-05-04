"""Handler for /regions — user preferred region selection."""

import asyncio
import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.handlers.filters import PrivateChatOnlyFilter
from src.handlers.helpers import (
    _go_main_menu,
    dismiss_reply_keyboard,
    safe_callback_answer,
    safe_edit_message,
)
from src.keyboards.inline import create_region_keyboard
from src.services.container import ServiceContainer
from src.services.states import RegionStates, UserUpdateStates
from src.utils.callback_factories import (
    MainMenuActions,
    MainMenuCallback,
    RegionActions,
    RegionCallback,
)
from src.utils.i18n import gettext as _
from src.utils.regions import REGION_SLUGS

logger = logging.getLogger(__name__)
router = Router(name="regions")


async def _start_region_selection(
    telegram_id: int,
    message: Message,
    services: ServiceContainer,
    state: FSMContext,
    edit: bool = False,
) -> None:
    """Send or edit the region picker — shared entry for command and main-menu button.

    When ``edit`` is True the existing ``message`` is edited in place (used for the
    main-menu callback path so the main menu message morphs into the region picker).
    Otherwise a new message is sent (used for the /regions command path).
    """
    user = await services.user_service.get_user(telegram_id)

    if not user:
        await message.answer(_("ask_user_name", locale="uz"))
        await state.set_state(UserUpdateStates.ASK_USER_NAME)
        return

    user_lang = (user or {}).get("language", "ru")
    current_regions: list[str] = (user or {}).get("preferred_regions", [])

    await state.set_state(RegionStates.SELECTING)
    await state.update_data(selected_slugs=current_regions)

    text = _("select_regions", locale=user_lang)
    keyboard = create_region_keyboard(current_regions, user_lang)

    if edit:
        await safe_edit_message(message, text, reply_markup=keyboard)
    else:
        await dismiss_reply_keyboard(message, "📍")
        await message.answer(text, reply_markup=keyboard)


@router.message(PrivateChatOnlyFilter(), Command(commands=["regions", "region"]))
async def handle_regions_command(
    message: Message,
    services: ServiceContainer,
    state: FSMContext,
) -> None:
    """Show region preference selection keyboard (via /regions command)."""
    await _start_region_selection(message.from_user.id, message, services, state)


@router.callback_query(MainMenuCallback.filter(F.action == MainMenuActions.SELECT_REGIONS))
async def handle_regions_menu_button(
    callback: CallbackQuery,
    services: ServiceContainer,
    state: FSMContext,
) -> None:
    """Show region preference selection keyboard (via main menu button)."""
    await safe_callback_answer(callback)
    await _start_region_selection(callback.from_user.id, callback.message, services, state, edit=True)


@router.callback_query(RegionStates.SELECTING, RegionCallback.filter())
async def handle_region_callback(
    callback: CallbackQuery,
    callback_data: RegionCallback,
    services: ServiceContainer,
    state: FSMContext,
) -> None:
    """Handle toggle / select-all / unselect-all / save callbacks."""
    user = await services.user_service.get_user(callback.from_user.id)
    user_lang = (user or {}).get("language", "ru")

    data = await state.get_data()
    selected: list[str] = list(data.get("selected_slugs", []))

    action = callback_data.action

    if action == RegionActions.TOGGLE:
        slug = callback_data.slug
        if slug in selected:
            selected.remove(slug)
        else:
            selected.append(slug)
        await state.update_data(selected_slugs=selected)
        await callback.message.edit_reply_markup(reply_markup=create_region_keyboard(selected, user_lang))
        await callback.answer()

    elif action == RegionActions.SELECT_ALL:
        selected = list(REGION_SLUGS)
        await state.update_data(selected_slugs=selected)
        await callback.message.edit_reply_markup(reply_markup=create_region_keyboard(selected, user_lang))
        await callback.answer()

    elif action == RegionActions.UNSELECT_ALL:
        selected = []
        await state.update_data(selected_slugs=selected)
        await callback.message.edit_reply_markup(reply_markup=create_region_keyboard(selected, user_lang))
        await callback.answer()

    elif action == RegionActions.SAVE:
        updated = await services.user_service.update_user(
            telegram_id=callback.from_user.id,
            user_data={"preferred_regions": selected},
        )
        await state.clear()
        if updated:
            # First: edit to "saved" confirmation with no keyboard.
            await safe_edit_message(
                callback.message,
                _("regions_saved", locale=user_lang),
                reply_markup=None,
            )
            await callback.answer()
            # Then: after a short pause, morph back into the main menu.
            await asyncio.sleep(1)
            await _go_main_menu(
                callback.from_user.id,
                callback.message,
                state,
                services,
                user_lang,
            )
        else:
            await callback.answer(_("error_occurred", locale=user_lang))
