from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from src.utils.i18n import gettext as _


def create_skip_keyboard(user_lang: str) -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=_("skip_button", locale=user_lang))]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    return keyboard


def create_cancel_keyboard(user_lang: str) -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=_("cancel_button", locale=user_lang))]],
        resize_keyboard=True,
        one_time_keyboard=True,
        selective=True,
    )

    return keyboard


def create_resume_confirmation_keyboard(user_lang: str) -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=_("confirm_button", locale=user_lang))],
            [KeyboardButton(text=_("cancel_button", locale=user_lang))],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    return keyboard
