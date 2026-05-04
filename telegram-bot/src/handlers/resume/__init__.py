"""Resume handlers package."""

from aiogram import Router

from .credits import router as credits_router
from .helpers import image_bytes_to_data_uri
from .qa_creation import router as qa_router
from .upload import router as upload_router
from .view import router as view_router

router = Router(name="resume")
router.include_router(qa_router)
router.include_router(upload_router)
router.include_router(view_router)
router.include_router(credits_router)


__all__ = ["image_bytes_to_data_uri", "router"]
