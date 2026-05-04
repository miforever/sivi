"""Dependency injection utilities for handlers."""

import logging

from aiogram import Dispatcher

from src.services.container import ServiceContainer

# Configure logger
logger = logging.getLogger(__name__)


def setup_deps(dispatcher: Dispatcher, services: ServiceContainer) -> None:
    """
    Setup dependency injection for the dispatcher.

    Args:
        dispatcher: The aiogram dispatcher instance
        services: Service container with all services
    """
    if not dispatcher:
        raise ValueError("Dispatcher cannot be None")

    if not services:
        raise ValueError("Service container cannot be None")

    # Store services in dispatcher for backward compatibility
    dispatcher["services"] = services

    # Register language middleware
    from src.middlewares.language import LanguageMiddleware

    dispatcher.message.middleware(LanguageMiddleware(services))
    dispatcher.callback_query.middleware(LanguageMiddleware(services))

    # Register throttling middleware
    # from src.middlewares.throttling import ThrottlingMiddleware
    # dispatcher.message.middleware(ThrottlingMiddleware(services))
    # dispatcher.callback_query.middleware(ThrottlingMiddleware(services))

    # Register logging middleware if it exists
    try:
        from src.middlewares.logging import LoggingMiddleware

        dispatcher.message.middleware(LoggingMiddleware())
        dispatcher.callback_query.middleware(LoggingMiddleware())
    except ImportError:
        logger.debug("LoggingMiddleware not found, skipping")

    logger.info("Dependencies setup completed")
