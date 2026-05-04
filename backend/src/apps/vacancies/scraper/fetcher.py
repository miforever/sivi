"""Async Telegram message fetcher using Telethon."""

from telethon import TelegramClient
from telethon.tl.types import (
    MessageEntityBold,
    MessageEntityCode,
    MessageEntityHashtag,
    MessageEntityItalic,
    MessageEntityMention,
    MessageEntityPhone,
    MessageEntityTextUrl,
    MessageEntityUrl,
)


def _serialize_entity(entity) -> dict:
    """Convert a Telegram MessageEntity to a serializable dict."""
    base = {
        "type": type(entity).__name__,
        "offset": entity.offset,
        "length": entity.length,
    }
    if isinstance(entity, MessageEntityTextUrl):
        base["url"] = entity.url
    type_map = {
        MessageEntityMention: "mention",
        MessageEntityHashtag: "hashtag",
        MessageEntityUrl: "url",
        MessageEntityBold: "bold",
        MessageEntityItalic: "italic",
        MessageEntityCode: "code",
        MessageEntityPhone: "phone",
    }
    for cls, name in type_map.items():
        if isinstance(entity, cls):
            base["type"] = name
            break
    return base


async def fetch_channel_messages(
    client: TelegramClient,
    channel_username: str,
    limit: int = 50,
    min_id: int = 0,
) -> list[dict]:
    """Fetch recent messages from a public Telegram channel.

    Args:
        client: Connected Telethon client.
        channel_username: Channel username (without @).
        limit: Max messages to fetch.
        min_id: Only fetch messages with ID > min_id (for incremental scraping).

    Returns:
        List of serialized message dicts.
    """
    entity = await client.get_entity(channel_username)

    messages = []
    async for msg in client.iter_messages(entity, limit=limit, min_id=min_id):
        if not msg.text:
            continue

        messages.append(
            {
                "id": msg.id,
                "date": msg.date.isoformat() if msg.date else None,
                "text": msg.text or "",
                "raw_text": msg.raw_text or "",
                "entities": [_serialize_entity(e) for e in (msg.entities or [])],
                "views": msg.views,
                "forwards": msg.forwards,
                "media_type": type(msg.media).__name__ if msg.media else None,
                "reply_to_msg_id": msg.reply_to.reply_to_msg_id if msg.reply_to else None,
                "grouped_id": msg.grouped_id,
            }
        )

    return messages
