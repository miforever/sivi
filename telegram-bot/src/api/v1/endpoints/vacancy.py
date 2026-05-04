import logging
from enum import StrEnum
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.api.dependencies import (
    get_backend,
    get_bot,
    get_cache,
)
from src.handlers.helpers import send_vacancy
from src.utils.i18n import gettext as _

logger = logging.getLogger(__name__)

router = APIRouter()


class WorkLocation(StrEnum):
    REMOTE = "remote"
    ON_SITE = "onsite"
    HYBRID = "hybrid"


class VacancyRequest(BaseModel):
    title: str
    company: str
    department: str
    job_type: WorkLocation
    raw_salary: int
    min_salary: int
    max_salary: int
    currency: str
    experience_level: str
    skills: str
    location: str
    url: str


@router.post("/vacancy/send/{tg_id}")
async def matching_vacancy(
    tg_id: int,
    request: VacancyRequest,
    bot=Depends(get_bot),
    cache_service=Depends(get_cache),
    backend_service=Depends(get_backend),
) -> dict[str, Any]:

    try:
        if not isinstance(tg_id, int) or tg_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid telegram user ID",
            )

        # Get user language from cache
        user_lang = await cache_service.get_user_language(tg_id)

        # If not in cache, try backend
        if not user_lang:
            try:
                user_lang = await backend_service.get_user_language(tg_id)
                if user_lang:
                    # Update cache for future use
                    try:
                        await cache_service.set_user_language(tg_id, user_lang)
                    except Exception:
                        pass
            except Exception:
                pass

        # Use default if still not found
        if not user_lang:
            user_lang = "uz"  # Default language

        vacancy_data = {
            "title": request.title,
            "company": request.company,
            "department": request.department,
            "job_type": request.job_type,
            "raw_salary": request.raw_salary,
            "min_salary": request.min_salary,
            "max_salary": request.max_salary,
            "currency": request.currency,
            "experience_level": request.experience_level,
            "skills": request.skills,
            "location": request.location,
            "url": request.url,
        }

        await bot.send_message(
            tg_id,
            _("match_message", locale=user_lang),
            parse_mode="HTML",
        )

        if bot:
            notification_sent = await send_vacancy(
                bot,
                tg_id,
                user_lang,
                vacancy_data,
                cache_service,
                backend_service,
            )

            if not notification_sent:
                logger.warning("Failed to send notification to user %s", tg_id)

            # Return the vacancy data we received plus the target tg_id and timestamp
            return {
                "success": True,
                "message": "Vacancy notification sent",
                "data": {
                    "tg_id": tg_id,
                    "vacancy": vacancy_data,
                    "sent_at": "2024-01-15T10:30:00Z",
                },
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating application decision: %s", str(e), exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
