"""Photo upload and skip handling."""

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove

from src.handlers.filters import PrivateChatOnlyFilter
from src.utils.i18n import gettext as _

from ..states import ResumeState
from .confirmation import show_confirmation

logger = logging.getLogger(__name__)
router = Router(name="resume_qa_photo")


@router.message(PrivateChatOnlyFilter(), ResumeState.UPLOAD_PHOTO, F.photo)
async def handle_photo_upload(
    message: Message,
    state: FSMContext,
    user_lang: str | None = None,
) -> None:
    """Handle photo upload."""
    try:
        photo = message.photo[-1]
        await state.update_data(photo_file_id=photo.file_id)
        await show_confirmation(message, state, user_lang)
    except Exception as e:
        logger.error("Error handling photo: %s", str(e))
        await message.answer(_("error_occurred_retry", locale=user_lang))


@router.message(PrivateChatOnlyFilter(), ResumeState.UPLOAD_PHOTO, F.text)
async def handle_photo_skip(
    message: Message,
    state: FSMContext,
    user_lang: str | None = None,
) -> None:
    """Handle photo skip."""
    if message.text.strip() == _("skip_button", locale=user_lang):
        try:
            await message.answer(" ", reply_markup=ReplyKeyboardRemove())
        except Exception:
            pass
        await show_confirmation(message, state, user_lang)
    else:
        skip_keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=_("skip_button", locale=user_lang))]],
            resize_keyboard=True,
            one_time_keyboard=True,
            selective=True,
        )
        await message.answer(_("upload_photo", locale=user_lang), reply_markup=skip_keyboard)
