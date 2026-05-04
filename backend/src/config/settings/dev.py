"""
Development settings for resume-vacancy-api project.
"""

from .base import *  # noqa: F403

INSTALLED_APPS += [  # noqa: F405
    "django_extensions",
]


INTERNAL_IPS = ["127.0.0.1", "localhost"]


# Allow all origins in development
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

# Disable secure SSL redirects in development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Log level for development
LOGGING["loggers"]["django"]["level"] = "DEBUG"  # noqa: F405
LOGGING["loggers"]["apps"]["level"] = "DEBUG"  # noqa: F405
