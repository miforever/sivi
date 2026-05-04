"""
Dependencies for API routes.

This module provides dependency injection for the API endpoints,
ensuring they have access to the necessary services and instances.
"""

import logging

from aiogram import Bot, Dispatcher

from src.services.backend import BackendService
from src.services.cache import Cache

logger = logging.getLogger(__name__)


class APIDependencies:
    """Container for API dependencies."""

    def __init__(self):
        self.bot: Bot | None = None
        self.dispatcher: Dispatcher | None = None
        self.cache: Cache | None = None
        self.backend: BackendService | None = None
        self.webhook_secret: str | None = None

    def set_bot(self, bot: Bot):
        """Set the bot instance."""
        self.bot = bot

    def set_dispatcher(self, dispatcher: Dispatcher):
        """Set the dispatcher instance."""
        self.dispatcher = dispatcher

    def set_cache(self, cache: Cache):
        """Set the cache service."""
        self.cache = cache

    def set_backend(self, backend: BackendService):
        """Set the backend service."""
        self.backend = backend

    def set_webhook_secret(self, secret: str):
        """Set the webhook secret."""
        self.webhook_secret = secret


api_deps = APIDependencies()


def get_bot() -> Bot | None:
    """Get the bot instance."""
    return api_deps.bot


def get_dispatcher() -> Dispatcher | None:
    """Get the dispatcher instance."""
    return api_deps.dispatcher


def get_cache() -> Cache | None:
    """Get the cache service."""
    return api_deps.cache


def get_backend() -> BackendService | None:
    """Get the backend service."""
    return api_deps.backend


def get_webhook_secret() -> str | None:
    """Get the webhook secret."""
    return api_deps.webhook_secret
