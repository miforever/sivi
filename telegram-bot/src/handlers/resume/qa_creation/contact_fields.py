"""Contact field (email/phone) input handlers."""

import logging

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.handlers.filters import PrivateChatOnlyFilter
from src.services.container import ServiceContainer
from src.utils.i18n import gettext as _
from src.utils.validators import validate_email, validate_phone

from ..helpers import handle_cancel_action, process_contact_fields
from ..states import ResumeState
from .finalization import finalize_qa_resume

logger = logging.getLogger(__name__)
router = Router(name="resume_qa_contact_fields")


@router.message(PrivateChatOnlyFilter(), ResumeState.ASK_EMAIL)
async def handle_email_input(
    message: Message,
    state: FSMContext,
    services: ServiceContainer,
    user_lang: str,
) -> None:
    """Handle email input."""
    try:
        if message.text == _("cancel_button", locale=user_lang):
            await handle_cancel_action(message, state, services, message.from_user.id, user_lang)
            return

        data = await state.get_data()
        from_qa_flow = data.get("from_qa_flow", False)
        resume_data = data.get("qa_resume_data" if from_qa_flow else "parsed_resume_data", {})

        if message.text == _("skip_button", locale=user_lang):
            if resume_data.get("phone", "").strip():
                missing_fields = data.get("missing_contact_fields", [])
                if "email" in missing_fields:
                    missing_fields.remove("email")
                await state.update_data(missing_contact_fields=missing_fields)
                await process_next_contact_field(message, state, services, user_lang)
                return
            await message.answer(_("cannot_skip_contact_field", locale=user_lang))
            return

        email = message.text.strip()
        if not validate_email(email):
            await message.answer(_("invalid_email", locale=user_lang))
            return

        resume_data["email"] = email
        missing_fields = data.get("missing_contact_fields", [])
        if "email" in missing_fields:
            missing_fields.remove("email")

        key = "qa_resume_data" if from_qa_flow else "parsed_resume_data"
        await state.update_data(**{key: resume_data, "missing_contact_fields": missing_fields})
        await process_next_contact_field(message, state, services, user_lang)

    except Exception as e:
        logger.error("Error handling email: %s", str(e))
        await message.answer(_("error_occurred_general", locale=user_lang))
        await state.clear()


@router.message(PrivateChatOnlyFilter(), ResumeState.ASK_PHONE)
async def handle_phone_input(
    message: Message,
    state: FSMContext,
    services: ServiceContainer,
    user_lang: str | None = None,
) -> None:
    """Handle phone input."""
    try:
        if message.text == _("cancel_button", locale=user_lang):
            await handle_cancel_action(message, state, services, message.from_user.id, user_lang)
            return

        data = await state.get_data()
        from_qa_flow = data.get("from_qa_flow", False)
        resume_data = data.get("qa_resume_data" if from_qa_flow else "parsed_resume_data", {})

        if message.text == _("skip_button", locale=user_lang):
            if resume_data.get("email", "").strip():
                missing_fields = data.get("missing_contact_fields", [])
                if "phone" in missing_fields:
                    missing_fields.remove("phone")
                await state.update_data(missing_contact_fields=missing_fields)
                await process_next_contact_field(message, state, services, user_lang)
                return
            await message.answer(_("cannot_skip_contact_field", locale=user_lang))
            return

        phone = message.text.strip()
        if not validate_phone(phone):
            await message.answer(_("invalid_phone", locale=user_lang))
            return

        resume_data["phone"] = phone
        missing_fields = data.get("missing_contact_fields", [])
        if "phone" in missing_fields:
            missing_fields.remove("phone")

        key = "qa_resume_data" if from_qa_flow else "parsed_resume_data"
        await state.update_data(**{key: resume_data, "missing_contact_fields": missing_fields})
        await process_next_contact_field(message, state, services, user_lang)

    except Exception as e:
        logger.error("Error handling phone: %s", str(e))
        await message.answer(_("error_occurred_general", locale=user_lang))
        await state.clear()


async def process_next_contact_field(
    message: Message,
    state: FSMContext,
    services: ServiceContainer,
    user_lang: str,
) -> None:
    """Process next contact field or finalize resume."""
    data = await state.get_data()
    missing_fields = data.get("missing_contact_fields", [])
    from_qa_flow = data.get("from_qa_flow", False)

    if missing_fields:
        resume_data = data.get("qa_resume_data" if from_qa_flow else "parsed_resume_data", {})
        await process_contact_fields(message, state, missing_fields, resume_data, user_lang)
    else:
        if from_qa_flow:
            resume_data = data.get("qa_resume_data", {})
            photo_bytes = data.get("photo_bytes")
            resume_language = data.get("resume_language")
            await finalize_qa_resume(
                message, state, services, resume_data, photo_bytes, resume_language, message.from_user.id, user_lang
            )
        else:
            from ..upload import finalize_uploaded_resume

            await finalize_uploaded_resume(message, state, services, message.from_user.id, user_lang)
