"""Backend service module -- facade that preserves the original BackendService API."""

from src.services.backend.base import BackendServiceError, _BackendClient
from src.services.backend.credit import CreditAPI
from src.services.backend.event import EventAPI
from src.services.backend.matching import MatchingAPI
from src.services.backend.pdf import PDFAPI
from src.services.backend.question import QuestionAPI
from src.services.backend.resume import ResumeAPI
from src.services.backend.subscription import SubscriptionAPI
from src.services.backend.user import UserAPI
from src.services.backend.vacancy import VacancyAPI


class BackendService(
    UserAPI,
    ResumeAPI,
    PDFAPI,
    CreditAPI,
    VacancyAPI,
    MatchingAPI,
    SubscriptionAPI,
    QuestionAPI,
    EventAPI,
):
    """Facade that composes every domain API into a single service.

    All existing callers can continue to do:
        from src.services.backend import BackendService
    """

    def __init__(self) -> None:
        _BackendClient.__init__(self)


__all__ = [
    "PDFAPI",
    "BackendService",
    "BackendServiceError",
    "CreditAPI",
    "EventAPI",
    "MatchingAPI",
    "QuestionAPI",
    "ResumeAPI",
    "SubscriptionAPI",
    "UserAPI",
    "VacancyAPI",
]
