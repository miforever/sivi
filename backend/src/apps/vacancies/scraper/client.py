"""Telethon client factory for Telegram channel scraping."""

from django.conf import settings
from telethon import TelegramClient
from telethon.sessions import StringSession


def get_client() -> TelegramClient:
    """Create a Telethon client using the StringSession from settings.

    Returns an unconnected client — caller must connect/disconnect.
    """
    return TelegramClient(
        StringSession(settings.TELETHON_SESSION),
        settings.TELETHON_API_ID,
        settings.TELETHON_API_HASH,
    )
