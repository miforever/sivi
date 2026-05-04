"""
Main application entry point for the Sivi Telegram Bot.

This module initializes the bot, sets up the FastAPI application,
and configures the webhook for receiving updates from Telegram.
"""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager

import uvicorn
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.exceptions import TelegramNetworkError
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.strategy import FSMStrategy
from aiogram.types import BotCommand
from aiohttp import ClientTimeout
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.api.dependencies import api_deps
from src.api.v1.routes import router as api_router
from src.config import get_settings
from src.handlers import (
    career_tips,
    commands,
    feedback,
    interview_practice,
    job_search,
    language,
    main_menu,
    regions,
    resume,
    subscription,
    unknown,
    user_ops,
)
from src.middlewares.services import ServicesMiddleware
from src.services.container import ServiceContainer
from src.utils.deps import setup_deps


def setup_logging(log_level: str = "INFO") -> None:
    """Configure logging with the specified level."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
        force=True,
    )


logger = logging.getLogger(__name__)


class BotApplication:
    """Main bot application class that manages bot lifecycle."""

    def __init__(self):
        self.settings = get_settings()
        setup_logging(self.settings.LOG_LEVEL)
        self.bot: Bot | None = None
        self.dispatcher: Dispatcher | None = None
        self.services: ServiceContainer | None = None

    async def register_commands(self, bot: Bot) -> None:
        """Register bot commands."""
        commands_list = [
            BotCommand(command="start", description="🚀 Запустить бота"),
            BotCommand(command="resumes", description="📂 Просмотр резюме"),
            BotCommand(command="language", description="🌍 Изменить язык"),
            BotCommand(command="regions", description="📍 Регионы для поиска работы"),
            BotCommand(command="name", description="✏️ Изменить имя"),
            BotCommand(command="help", description="❓ Помощь"),
        ]

        try:
            await bot.set_my_commands(commands_list)
            logger.info("Bot commands registered successfully")
        except TelegramNetworkError as e:
            logger.warning(f"Failed to register commands (timeout): {e}. Bot will still function.")
        except Exception as e:
            logger.error(f"Unexpected error registering commands: {e}")

    async def setup_services(self) -> None:
        """Initialize and setup all services."""
        try:
            self.services = await ServiceContainer.create()
            logger.info("All services initialized successfully")
        except Exception as e:
            logger.error("Failed to setup services: %s", str(e))
            raise

    async def setup_bot_and_dispatcher(self) -> tuple[Bot, Dispatcher]:
        """Setup bot and dispatcher instances."""
        # Create dispatcher
        dp = Dispatcher(
            storage=MemoryStorage(),
            fsm_strategy=FSMStrategy.CHAT,
            events_isolation=None,
        )

        # Register middleware to inject services into all handlers
        services_middleware = ServicesMiddleware(self.services)
        dp.message.middleware(services_middleware)
        dp.callback_query.middleware(services_middleware)

        # Include routers
        dp.include_router(commands.router)
        dp.include_router(language.router)
        dp.include_router(regions.router)
        dp.include_router(main_menu.router)
        dp.include_router(user_ops.router)
        dp.include_router(resume.router)
        dp.include_router(job_search.router)
        dp.include_router(subscription.router)
        dp.include_router(feedback.router)
        dp.include_router(interview_practice.router)
        dp.include_router(career_tips.router)
        dp.include_router(unknown.router)

        AiohttpSession(timeout=ClientTimeout(total=60, connect=30, sock_read=30))

        # Create bot
        bot = Bot(
            token=self.settings.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode="HTML"),
        )

        # Setup shared dependencies (for backward compatibility)
        setup_deps(dp, self.services)

        return bot, dp

    async def setup_webhook(self, bot: Bot) -> None:
        """Setup webhook for the bot."""
        webhook_url = self.settings.get_webhook_url()
        webhook_info = await bot.get_webhook_info()

        if webhook_info.url != webhook_url:
            await bot.set_webhook(
                url=webhook_url,
                secret_token=self.settings.WEBHOOK_SECRET,
                drop_pending_updates=True,
                allowed_updates=[
                    "message",
                    "callback_query",
                    "pre_checkout_query",
                    "successful_payment",
                ],
            )
            logger.info("Webhook set to %s", webhook_url)

    async def cleanup_resources(self):
        """Cleanup application resources."""
        logger.info("Cleaning up resources...")

        # Close bot session if it exists
        if self.bot and hasattr(self.bot, "session"):
            await self.bot.session.close()

        # Close all services
        if self.services:
            await self.services.close()

        logger.info("Cleanup completed")

    async def start_polling(self) -> None:
        """Start the bot in polling mode."""
        try:
            await self.setup_services()
            self.bot, self.dispatcher = await self.setup_bot_and_dispatcher()
            await self.register_commands(self.bot)

            logger.info("Starting bot in polling mode...")
            await self.dispatcher.start_polling(
                self.bot, allowed_updates=self.dispatcher.resolve_used_update_types(), skip_updates=True
            )
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, shutting down...")
        except Exception as e:
            logger.error(f"Error running bot: {e}", exc_info=True)
        finally:
            await self.cleanup_resources()

    def create_fastapi_app(self) -> FastAPI:
        """Create and configure the FastAPI application."""

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            """Manage the application lifecycle."""
            try:
                # Setup services first
                await self.setup_services()

                # Setup bot and dispatcher
                self.bot, self.dispatcher = await self.setup_bot_and_dispatcher()

                # Set up API dependencies
                api_deps.set_bot(self.bot)
                api_deps.set_dispatcher(self.dispatcher)
                api_deps.set_cache(self.services.cache)
                api_deps.set_backend(self.services.backend)
                api_deps.set_webhook_secret(self.settings.WEBHOOK_SECRET)

                # Register commands
                await self.register_commands(self.bot)

                # Check if we should use webhook
                if self.settings.is_webhook_mode():
                    await self.setup_webhook(self.bot)
                    logger.info("Webhook setup completed")

                    yield

                    # Cleanup for webhook
                    await self.bot.delete_webhook(drop_pending_updates=True)
                else:
                    logger.info("Starting in polling mode...")

                    # Start polling in background
                    polling_task = asyncio.create_task(
                        self.dispatcher.start_polling(
                            self.bot, allowed_updates=self.dispatcher.resolve_used_update_types(), skip_updates=True
                        )
                    )

                    yield

                    # Cancel polling task
                    polling_task.cancel()
                    try:
                        await polling_task
                    except asyncio.CancelledError:
                        pass

            except Exception as e:
                logger.error(f"Error in application: {e}", exc_info=True)
                raise
            finally:
                await self.cleanup_resources()

        # Create FastAPI app with lifespan
        app = FastAPI(title="Sivi Bot API", description="API for Sivi Telegram Bot", version="1.0.0", lifespan=lifespan)

        # Include API routes
        app.include_router(api_router, prefix="/api")
        logger.info("API router included successfully")

        # Add health check endpoint
        @app.get("/health")
        async def health_check() -> dict[str, str]:
            """Health check endpoint for Docker."""
            return {"status": "ok"}

        # Register webhook endpoint
        @app.post("/webhook")
        async def webhook_handler(request: Request) -> JSONResponse:
            """Handle incoming webhook updates from Telegram."""
            # Verify secret token
            if self.settings.WEBHOOK_SECRET:
                secret_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
                if secret_token != self.settings.WEBHOOK_SECRET:
                    logger.warning("Invalid webhook secret token received")
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": "Invalid secret token"}
                    )

            # Parse and process the update
            try:
                raw = await request.json()
                logger.debug("Incoming webhook update: %s", list(raw.keys()) if isinstance(raw, dict) else raw)

                update = types.Update(**(raw or {}))
                await self.dispatcher.feed_update(bot=self.bot, update=update)

                return JSONResponse(status_code=200, content={"status": "ok"})

            except Exception as e:
                logger.exception("Error processing webhook update: %s", e)
                return JSONResponse(status_code=500, content={"detail": "Internal server error"})

        return app


# Create global application instance
app_instance = BotApplication()


def get_app() -> FastAPI:
    """Get the FastAPI application instance."""
    return app_instance.create_fastapi_app()


async def run_bot_directly():
    """Run the bot directly without uvicorn for development."""
    await app_instance.start_polling()


if __name__ == "__main__":
    # For development, run bot directly
    if not app_instance.settings.is_webhook_mode():
        logger.info("Running bot in development mode (polling)...")
        asyncio.run(run_bot_directly())
    else:
        # For production, run with uvicorn
        logger.info("Running bot in production mode (webhook)...")
        uvicorn.run(
            "src.main:get_app",
            host=app_instance.settings.HOST,
            port=app_instance.settings.PORT,
            reload=app_instance.settings.RELOAD,
            log_level=app_instance.settings.LOG_LEVEL.lower(),
        )
