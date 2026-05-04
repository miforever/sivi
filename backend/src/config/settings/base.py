"""
Base settings for resume-vacancy-api project.
Shared configuration for all environments.
"""

import os
from pathlib import Path

import environ
import structlog
from structlog.processors import JSONRenderer
from structlog.stdlib import ProcessorFormatter

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent
APPS_DIR = BASE_DIR / "apps"

# Environment variables
env = environ.Env(
    DEBUG=(bool, False),
    SECRET_KEY=(str, "insecure-secret-key"),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    DB_ENGINE=(str, "django.db.backends.sqlite3"),
    DB_NAME=(str, str(BASE_DIR / "db.sqlite3")),
    DB_USER=(str, ""),
    DB_PASSWORD=(str, ""),
    DB_HOST=(str, ""),
    DB_PORT=(int, 5432),
    USE_S3=(bool, False),
    AWS_STORAGE_BUCKET_NAME=(str, ""),
    AWS_S3_REGION_NAME=(str, "us-east-1"),
    CORS_ALLOWED_ORIGINS=(list, ["http://localhost:3000"]),
    API_KEYS=(list, []),
    MAX_FILE_SIZE=(int, 10485760),  # 10 MB
    ALLOWED_FILE_TYPES=(list, ["pdf", "doc", "docx"]),
    MAX_RESUMES_PER_USER=(int, 5),
    REDIS_URL=(str, "redis://localhost:6379/2"),
    SENTRY_DSN=(str, ""),
    LOG_LEVEL=(str, "INFO"),
)

environ.Env.read_env(str(BASE_DIR.parent / ".env"))

REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/2")

# =============================================================================
# Celery
# =============================================================================
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Asia/Tashkent"

# Core settings
DEBUG = env("DEBUG")
SECRET_KEY = env("SECRET_KEY")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# Application definition
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "corsheaders",
    "drf_spectacular",
    "django_filters",
]

LOCAL_APPS = [
    "apps.users",
    "apps.questions",
    "apps.resumes",
    "apps.store",
    "apps.vacancies",
    "apps.subscriptions",
    "apps.promocodes",
    "apps.referrals",
    "apps.common",
    "apps.matching",
    "apps.analytics",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Database
DATABASES = {
    "default": {
        "ENGINE": env("DB_ENGINE"),
        "NAME": env("DB_NAME"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST"),
        "PORT": env("DB_PORT"),
        "CONN_MAX_AGE": 600,
        "OPTIONS": {
            "connect_timeout": 10,
        }
        if env("DB_ENGINE") == "django.db.backends.postgresql"
        else {},
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
LOCALE_PATHS = [BASE_DIR / "locale"]

STATIC_URL = "/static/"
STATICFILES_DIRS = []
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Custom user model
AUTH_USER_MODEL = "users.User"

# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "apps.common.pagination.StandardPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.common.authentication.ApiKeyAuthentication",
        "apps.common.authentication.TelegramBotAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "apps.common.exceptions.custom_exception_handler",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
        "vacancy_search": "30/minute",
    },
}

# CORS Configuration
CORS_ALLOWED_ORIGINS = [*env("CORS_ALLOWED_ORIGINS"), "https://sivi.uz", "https://admin.sivi.uz"]
CORS_ALLOW_CREDENTIALS = True

# JWT Configuration
from datetime import timedelta  # noqa: E402

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# API Configuration
API_KEYS = env.list("API_KEYS")
MAX_FILE_SIZE = env("MAX_FILE_SIZE")
ALLOWED_FILE_TYPES = env("ALLOWED_FILE_TYPES")
MAX_RESUMES_PER_USER = env("MAX_RESUMES_PER_USER")

# DRF Spectacular Configuration
SPECTACULAR_SETTINGS = {
    "TITLE": "Sivi API",
    "DESCRIPTION": "Django REST API for Resume and Vacancy Management",
    "VERSION": "1.0.0",
    "SERVE_PERMISSIONS": ["rest_framework.permissions.AllowAny"],
    "SWAGGER_UI_SETTINGS": {
        "persistAuthorization": True,
        "displayOperationId": True,
    },
    "SERVERS": [
        {"url": "http://localhost:8000", "description": "Development"},
        {"url": "https://api.example.com", "description": "Production"},
    ],
}

# Logging Configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "json": {
            "()": ProcessorFormatter,
            "processor": JSONRenderer(),
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs" / "django.log",
            "maxBytes": 1024 * 1024 * 10,  # 10 MB
            "backupCount": 5,
            "formatter": "json",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": env("LOG_LEVEL"),
            "propagate": False,
        },
        "apps": {
            "handlers": ["console", "file"],
            "level": env("LOG_LEVEL"),
            "propagate": False,
        },
    },
}

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

# Create logs directory if it doesn't exist
os.makedirs(BASE_DIR / "logs", exist_ok=True)

# =============================================================================
# Embedding / Matching Configuration
# =============================================================================
FIREWORKS_API_KEY = env("FIREWORKS_API_KEY", default="")
FIREWORKS_EMBEDDING_MODEL = env("FIREWORKS_EMBEDDING_MODEL", default="WhereIsAI/UAE-Large-V1")
EMBEDDING_DIMENSIONS = env.int("EMBEDDING_DIMENSIONS", default=1024)

# =============================================================================
# Telegram Scraper (Telethon)
# =============================================================================
TELETHON_API_ID = env.int("TELETHON_API_ID", default=0)
TELETHON_API_HASH = env("TELETHON_API_HASH", default="")
TELETHON_BOT_TOKEN = env("TELETHON_BOT_TOKEN", default="")
TELETHON_SESSION = env("TELETHON_SESSION", default="")

# =============================================================================
# Telegram Job Aggregation — Channels to scrape/monitor for vacancies
# =============================================================================
TELEGRAM_JOB_CHANNELS = {
    "clozjobs": {
        "name": "Tashkent Jobs",
        "language": "uz",  # bilingual titles but primarily Uzbek
        "category": "general",
        "priority": 1,
    },
    "uzdev_jobs": {
        "name": "UzDev Jobs – IT Jobs",
        "language": "ru",
        "category": "it",
        "priority": 1,
    },
    "UstozShogird": {
        "name": "Ustoz-Shogird",
        "language": "uz",
        "category": "mentorship",
        "priority": 1,
    },
    "python_djangojobs": {
        "name": "Python Jobs",
        "language": "ru",
        "category": "it",
        "priority": 2,
    },
    "data_ish": {
        "name": "DATA | ISH",
        "language": "uz",
        "category": "data",
        "priority": 2,
    },
    "UzjobsUz": {
        "name": "UzJobs.uz",
        "language": "ru",
        "category": "professional",
        "priority": 2,
    },
    "edu_vakansiya": {
        "name": "Edu Vakansiya",
        "language": "uz",
        "category": "education",
        "priority": 2,
    },
    "click_jobs": {
        "name": "Click Jobs",
        "language": "uz",
        "category": "it",
        "priority": 3,
    },
    "Exampleuz": {
        "name": "Example.uz - IT Jobs",
        "language": "uz",
        "category": "it",
        "priority": 3,
    },
    "itpark_uz": {
        "name": "IT Park Uzbekistan",
        "language": "uz",
        "category": "it",
        "priority": 1,
    },
    "doda_jobs": {
        "name": "Doda Jobs - Работа в Ташкенте",
        "language": "ru",
        "category": "general",
        "priority": 2,
    },
    "uzbekistanishborwork": {
        "name": "TashJob - Uzbekistan ishbor",
        "language": "ru",
        "category": "general",
        "priority": 3,
    },
    "ITjobs_Uzbekistan": {
        "name": "Uzbekistan IT Jobs",
        "language": "ru",
        "category": "it",
        "priority": 3,
    },
    "hrjobuz": {
        "name": "HR job Uzbekistan",
        "language": "ru",
        "category": "hr",
        "priority": 3,
    },
    "vacancyuzairports": {
        "name": "Vacancy Uzbekistan Airports",
        "language": "uz",
        "category": "general",
        "priority": 1,
    },
    "linkedinjobsuzbekistan": {
        "name": "LinkedIn Jobs Uzbekistan",
        "language": "en",
        "category": "professional",
        "priority": 2,
    },
    "ishmi_ish": {
        "name": "Ishmi-ish | IT va Boshqa Vakansiyalar",
        "language": "uz",
        "category": "general",
        "priority": 3,
    },
}

# =============================================================================
# Platform (API/website) Vacancy Sources
# =============================================================================
PLATFORM_SOURCES = {
    "hh_uz": {"name": "hh.uz"},
    "olx_uz": {"name": "OLX.uz"},
    "vacandi_uz": {"name": "Vacandi.uz"},
    "ishkop_uz": {"name": "Ishkop.uz"},
    "uzairways": {"name": "Uzbekistan Airways"},
}

# Sentry Configuration
if env("SENTRY_DSN"):
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=env("SENTRY_DSN"),
        integrations=[DjangoIntegration()],
        traces_sample_rate=1.0,
        send_default_pii=False,
    )
