"""Q&A based resume creation handlers."""

from aiogram import Router

from .confirmation import router as confirmation_router
from .contact_fields import router as contact_fields_router
from .finalization import router as finalization_router
from .photo import router as photo_router
from .questions import router as questions_router
from .start import router as start_router

router = Router(name="resume_qa")
router.include_router(start_router)
router.include_router(questions_router)
router.include_router(photo_router)
router.include_router(confirmation_router)
router.include_router(contact_fields_router)
router.include_router(finalization_router)

__all__ = ["router"]
