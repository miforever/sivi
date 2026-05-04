"""Helper functions for resume creation and upload flows."""

import base64
import logging

from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from src.handlers.helpers import _go_main_menu
from src.services.container import ServiceContainer
from src.utils.i18n import gettext as _

logger = logging.getLogger(__name__)


def image_bytes_to_data_uri(image_bytes: bytes) -> str:
    """Convert image bytes to base64 data URI."""
    base64_str = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:image/png;base64,{base64_str}"


async def validate_resume_fields(resume_data: dict) -> tuple[list[str], list[str]]:
    """
    Validate resume fields and return missing required and contact fields.

    Returns:
        Tuple of (missing_required_fields, missing_contact_fields)
    """
    missing_required = []
    missing_contact = []

    # Check required fields
    if not resume_data.get("full_name", "").strip():
        missing_required.append("full_name")
    if not resume_data.get("location", "").strip():
        missing_required.append("location")

    # Check contact fields - at least one must be present
    has_email = bool(resume_data.get("email", "").strip())
    has_phone = bool(resume_data.get("phone", "").strip())

    if not has_email and not has_phone:
        # No contact method provided, both are required initially
        missing_contact = ["email", "phone"]
    else:
        # If one is provided, the other is optional (skippable)
        if not has_email:
            missing_contact.append("email")
        if not has_phone:
            missing_contact.append("phone")

    return missing_required, missing_contact


async def handle_cancel_action(
    message: Message, state: FSMContext, services: ServiceContainer, user_id: int, user_lang: str
) -> None:
    """
    Handle cancel action during resume creation flow.
    Clears state and returns to main menu.
    """
    try:
        await message.answer(_("resume_creation_cancelled", locale=user_lang), reply_markup=ReplyKeyboardRemove())
        await services.cache.clear_resume_answers(user_id)
        await state.clear()
        await _go_main_menu(user_id, message, state, services, user_lang, send_new=True)
    except Exception as e:
        logger.error("Error handling cancel action for user %s: %s", user_id, str(e))
        await message.answer(_("error_occurred_general", locale=user_lang))
        await state.clear()


async def save_resume_to_backend(
    message: Message,
    resume_data: dict,
    services: ServiceContainer,
    user_id: int,
    user_lang: str | None = None,
    state: FSMContext | None = None,
) -> dict | None:
    """
    Save resume to backend service.

    Args:
        message: Telegram message object
        resume_data: Resume data dictionary
        files_dict: Dictionary of file bytes {field_name: bytes}
        services: Service container
        user_lang: User's language code
        state: FSM context (optional, used for error handling)

    Returns:
        Saved resume data from backend or None if failed
    """
    try:
        saved_resume = await services.backend.save_resume(user_id, resume_data)
        if not saved_resume or saved_resume.get("error"):
            logger.error("Backend rejected resume for user %s: %s", user_id, saved_resume)
            return None

        return saved_resume

    except Exception as e:
        logger.error("Backend service error during resume save for user %s: %s", user_id, str(e))

        # Check if it's a resume limit error
        if "RESUME_LIMIT_REACHED" in str(e):
            if state:
                await _go_main_menu(user_id, message, state, services, user_lang)
            return None

        # Check if it's an email validation error
        if "error.validation_error" in str(e) and "email" in str(e):
            return None

        # Other backend errors
        if state:
            await _go_main_menu(user_id, message, state, services, user_lang)
        return None


async def update_cache_with_resume(user_id: int, saved_resume: dict, services: ServiceContainer) -> None:
    """
    Update user's resume cache after successful save.

    Args:
        user_id: Telegram user ID
        saved_resume: Resume data returned from backend
        services: Service container
    """
    try:
        user_resumes = await services.cache.get_user_resumes(user_id)
        if not user_resumes:
            user_resumes = await services.backend.get_user_resumes(user_id)
            await services.cache.save_user_resumes(user_id, user_resumes)
        else:
            user_resumes.append(saved_resume)
            await services.cache.save_user_resumes(user_id, user_resumes)

        logger.info("Successfully updated cache for user %s with %d resumes", user_id, len(user_resumes))
    except Exception as e:
        logger.warning("Failed to update cache for user %s: %s", user_id, str(e))
        # Continue execution even if cache update fails


async def process_contact_fields(
    message: Message, state: FSMContext, missing_fields: list[str], resume_data: dict, user_lang: str | None = None
) -> None:
    """
    Process missing contact fields by asking user for them.

    Args:
        message: Telegram message object
        state: FSM context
        missing_fields: List of missing contact field names
        resume_data: Current resume data
        user_lang: User's language code
    """
    if not missing_fields:
        return

    current_field = missing_fields[0]

    # Check if we already have one contact method (making the other skippable)
    has_email = bool(resume_data.get("email", "").strip())
    has_phone = bool(resume_data.get("phone", "").strip())
    is_skippable = has_email or has_phone

    from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

    if current_field == "email":
        keyboard_buttons = []
        if is_skippable:
            keyboard_buttons.append(KeyboardButton(text=_("skip_button", locale=user_lang)))
        keyboard_buttons.append(KeyboardButton(text=_("cancel_button", locale=user_lang)))

        keyboard = ReplyKeyboardMarkup(
            keyboard=[keyboard_buttons],
            resize_keyboard=True,
            one_time_keyboard=True,
            selective=True,
        )
        prompt_message = (
            _("please_provide_email_skippable", locale=user_lang)
            if is_skippable
            else _("please_provide_email", locale=user_lang)
        )
        await message.answer(prompt_message, reply_markup=keyboard)

        from .states import ResumeState

        await state.set_state(ResumeState.ASK_EMAIL)

    elif current_field == "phone":
        keyboard_buttons = []
        if is_skippable:
            keyboard_buttons.append(KeyboardButton(text=_("skip_button", locale=user_lang)))
        keyboard_buttons.append(KeyboardButton(text=_("cancel_button", locale=user_lang)))

        keyboard = ReplyKeyboardMarkup(
            keyboard=[keyboard_buttons],
            resize_keyboard=True,
            one_time_keyboard=True,
            selective=True,
        )
        prompt_message = (
            _("please_provide_phone_skippable", locale=user_lang)
            if is_skippable
            else _("please_provide_phone", locale=user_lang)
        )
        await message.answer(prompt_message, reply_markup=keyboard)

        from .states import ResumeState

        await state.set_state(ResumeState.ASK_PHONE)
