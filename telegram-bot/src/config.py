"""Configuration management for the Sivi Telegram bot."""

from functools import lru_cache

from pydantic import Field, HttpUrl, RedisDsn, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with validation and defaults."""

    # Application
    DEBUG: bool = Field(default=False, description="Debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    CLICK_TOKEN: str = Field(..., description="Click service token")
    HOST: str = Field(default="0.0.0.0", description="Host to bind to")
    PORT: int = Field(default=8001, ge=1, le=65535, description="Port to bind to")

    # Telegram
    BOT_TOKEN: str = Field(..., min_length=1, description="Telegram bot token")
    ADMIN_IDS: list[int] = Field(default_factory=list, description="Admin user IDs")

    @field_validator("ADMIN_IDS", mode="before")
    @classmethod
    def parse_admin_ids(cls, v: object) -> object:
        """Accept empty string as empty list."""
        if v == "" or v is None:
            return []
        return v

    SUBCRIPTION_DESCRIPTION_EN: str = Field(
        default="https://telegra.ph/Sivi-PRO--Everything-You-Need-to-Get-Hired-Faster-12-04",
        description="Description for the subscription feature",
    )
    SUBCRIPTION_DESCRIPTION_RU: str = Field(
        default="https://telegra.ph/Sivi-PRO--Vsyo-chto-nuzhno-dlya-bystrogo-trudoustrojstva-12-04",
        description="Description for the subscription feature",
    )
    SUBCRIPTION_DESCRIPTION_UZ: str = Field(
        default="https://telegra.ph/Sivi-PRO--Tezroq-ishga-joylashish-uchun-kerak-bolgan-hamma-narsa-12-04",
        description="Description for the subscription feature",
    )
    SUBCRIPTION_DESCRIPTION_UZ2: str = Field(
        default="https://telegra.ph/Sivi-PRO--Tezro%D2%9B-ishga-zhojlashish-uchun-kerak-b%D1%9Elgan-%D2%B3amma-narsa-12-11",
        description="Description for the subscription feature",
    )
    WEBHOOK_HOST: HttpUrl | None = Field(default=None, description="Webhook host URL")
    WEBHOOK_PATH: str = Field(default="/webhook", description="Webhook path")
    WEBHOOK_SECRET: str | None = Field(default=None, description="Webhook secret token")
    WEBHOOK_URL: HttpUrl | None = Field(default=None, description="Full webhook URL")

    # Redis
    REDIS_HOST: str = Field(default="localhost", description="Redis host")
    REDIS_PORT: int = Field(default=6379, ge=1, le=65535, description="Redis port")
    REDIS_DB: int = Field(default=0, ge=0, le=15, description="Redis database number")
    REDIS_URL: RedisDsn | None = Field(default=None, description="Redis connection URL")

    # Backend APIs
    BACKEND_URL: HttpUrl = Field(..., description="Backend API URL")
    BACKEND_API_KEY: str = Field(..., description="Backend API KEY")

    # Cache and session settings
    USER_CACHE_TTL: int = Field(default=3600, ge=60, description="User cache TTL in seconds")
    LANGUAGE_CACHE_TTL: int = Field(default=3600, ge=60, description="Language cache TTL in seconds")
    VACANCY_CACHE_TTL: int = Field(default=1800, ge=60, description="Vacancy cache TTL in seconds")
    RESUME_ANSWERS_TTL: int = Field(default=259200, ge=3600, description="Resume answers cache TTL in seconds (3 days)")
    RESUMES_CACHE_TTL: int = Field(default=3600, ge=300, description="Resumes list cache TTL in seconds (1 hour)")

    # Job search feed
    JOB_WINDOW_SIZE: int = Field(default=20, ge=5, description="Jobs per matching window")
    JOB_MAX_SEEN: int = Field(default=1500, ge=100, description="Max seen jobs before ending feed")

    # Rate limiting
    THROTTLE_RATE: int = Field(default=3, ge=1, description="Rate limit per time window")
    THROTTLE_WINDOW: int = Field(default=60, ge=10, description="Rate limit time window in seconds")

    # Request timeout settings
    REQUEST_TIMEOUT: int = Field(default=30, ge=5, description="General request timeout in seconds")

    # File upload settings
    MAX_RESUME_SLOTS: int = Field(default=3, ge=1, description="Maximum number of resume slots per user")
    MAX_FILE_SIZE: int = Field(default=10 * 1024 * 1024, ge=1024 * 1024, description="Maximum file size in bytes")
    ALLOWED_EXTENSIONS: list[str] = Field(
        default_factory=lambda: [".pdf", ".doc", ".docx"], description="Allowed file extensions"
    )

    @field_validator("ALLOWED_EXTENSIONS", mode="before")
    @classmethod
    def parse_allowed_extensions(cls, v: object) -> object:
        """Accept comma-separated string or empty value."""
        if v == "" or v is None:
            return [".pdf", ".doc", ".docx"]
        if isinstance(v, str) and not v.startswith("["):
            return [ext.strip() for ext in v.split(",")]
        return v

    class Config:
        extra = "ignore"
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    @field_validator("REDIS_URL", mode="before")
    @classmethod
    def assemble_redis_url(cls, v, info) -> str:
        """Assemble Redis URL if not explicitly provided."""
        if isinstance(v, str):
            return v
        values = info.data
        if values.get("REDIS_HOST") and values.get("REDIS_PORT"):
            return f"redis://{values.get('REDIS_HOST')}:{values.get('REDIS_PORT')}/{values.get('REDIS_DB')}"
        return None

    @field_validator("WEBHOOK_URL", mode="before")
    @classmethod
    def assemble_webhook_url(cls, v, info) -> str | None:
        """Assemble webhook URL if not explicitly provided."""
        if isinstance(v, str):
            return v
        values = info.data
        if values.get("WEBHOOK_HOST") and values.get("WEBHOOK_PATH"):
            return f"{values.get('WEBHOOK_HOST')}{values.get('WEBHOOK_PATH')}"
        return None

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level '{v}'. Must be one of: {valid_levels}")
        return v_upper

    @field_validator("BOT_TOKEN")
    @classmethod
    def validate_bot_token(cls, v: str) -> str:
        """Validate bot token format."""
        if not v or len(v) < 10:
            raise ValueError("Bot token must be at least 10 characters long")
        return v

    def is_webhook_mode(self) -> bool:
        """Check if the application should run in webhook mode."""
        return bool(self.WEBHOOK_URL and self.WEBHOOK_SECRET)

    def get_webhook_url(self) -> str:
        """Get the full webhook URL."""
        if self.WEBHOOK_URL:
            return str(self.WEBHOOK_URL)
        if self.WEBHOOK_HOST and self.WEBHOOK_PATH:
            return f"{self.WEBHOOK_HOST}{self.WEBHOOK_PATH}"
        raise ValueError("Webhook URL not configured")

    def get_redis_url(self) -> str:
        """Get the Redis connection URL."""
        if self.REDIS_URL:
            return str(self.REDIS_URL)
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
