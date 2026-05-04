"""Service container for dependency management."""

from dataclasses import dataclass

from src.services.backend import BackendService
from src.services.cache import Cache
from src.services.resume_service import ResumeService
from src.services.subscription_service import SubscriptionService
from src.services.user_service import UserService


@dataclass
class ServiceContainer:
    """Container for all application services."""

    cache: Cache
    backend: BackendService
    user_service: UserService
    subscription_service: SubscriptionService
    resume_service: ResumeService

    @classmethod
    async def create(cls) -> "ServiceContainer":
        """Create and initialize all services."""
        cache = Cache()
        backend = BackendService()
        user_service = UserService(cache, backend)
        subscription_service = SubscriptionService(cache, backend)
        resume_service = ResumeService(cache, backend)

        return cls(
            cache=cache,
            backend=backend,
            user_service=user_service,
            subscription_service=subscription_service,
            resume_service=resume_service,
        )

    async def close(self):
        """Close all services."""
        await self.cache.close()
        await self.backend.close()
