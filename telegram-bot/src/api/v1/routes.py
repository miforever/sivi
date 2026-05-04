from fastapi import APIRouter

from .endpoints.health import router as health_router
from .endpoints.vacancy import router as vacancy_router

# Top-level router for all v1 endpoints.
router = APIRouter(prefix="/v1", tags=["api-v1"])

router.include_router(vacancy_router, prefix="/user")
router.include_router(health_router)
