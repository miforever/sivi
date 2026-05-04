"""QA resume finalization - PDF generation and saving."""

import asyncio
import logging

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, Message

from src.handlers.helpers import _go_main_menu
from src.services.container import ServiceContainer
from src.utils.i18n import gettext as _

from ..helpers import image_bytes_to_data_uri, save_resume_to_backend, update_cache_with_resume

logger = logging.getLogger(__name__)
router = Router(name="resume_qa_finalization")


async def finalize_qa_resume(
    message: Message,
    state: FSMContext,
    services: ServiceContainer,
    resume_data: dict,
    photo_bytes: bytes | None,
    resume_language: str,
    user_id: int,
    user_lang: str,
) -> None:
    """Finalize QA resume creation."""
    try:
        # Prepare profile image as data URI if provided
        profile_image = None
        if photo_bytes:
            profile_image = image_bytes_to_data_uri(photo_bytes)

        # Generate PDF using backend
        pdf_bytes = await services.backend.generate_pdf_from_resume(
            user_id,
            resume_data,
            profile_image=profile_image,
            language=resume_language,
        )

        if not pdf_bytes:
            await message.answer(_("ai_service_error", locale=user_lang))
            return

        resume_data["profile_image"] = profile_image
        resume_data["origin"] = "qa_generated"
        saved_resume = await save_resume_to_backend(
            message,
            resume_data,
            services,
            user_id,
            user_lang,
            state,
        )

        if not saved_resume:
            return

        await update_cache_with_resume(user_id, saved_resume, services)

        pdf_input = BufferedInputFile(pdf_bytes, filename="resume.pdf")
        await message.answer_document(pdf_input, caption=_("resume_created", locale=user_lang))
        await asyncio.sleep(1)
        await state.clear()
        await _go_main_menu(user_id, message, state, services, user_lang, send_new=True)

    except Exception as e:
        logger.error("Error finalizing QA resume: %s", str(e))
        await message.answer(_("ai_service_error", locale=user_lang))
