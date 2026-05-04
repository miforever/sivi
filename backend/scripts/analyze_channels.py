"""
Phase 1: Fetch raw posts from Telegram job channels for format analysis.

Connects to Telegram via Telethon using a bot token, pulls ~50 recent
messages from each configured channel, and saves them as JSON for review.

Usage:
    cd backend
    uv run python scripts/analyze_channels.py
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession
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

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / "src" / ".env"
SESSION_DIR = BASE_DIR / ".sessions"
OUTPUT_DIR = Path(__file__).resolve().parent / "output" / "raw"

CHANNELS = [
    "clozjobs",
    "uzdev_jobs",
    "UstozShogird",
    "python_djangojobs",
    "data_ish",
    "UzjobsUz",
    "edu_vakansiya",
    "click_jobs",
    "Exampleuz",
]

MESSAGES_PER_CHANNEL = 50

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def serialize_entity(entity) -> dict:
    """Convert a Telegram MessageEntity to a JSON-serializable dict."""
    base = {
        "type": type(entity).__name__,
        "offset": entity.offset,
        "length": entity.length,
    }
    if isinstance(entity, MessageEntityTextUrl):
        base["url"] = entity.url
    if isinstance(entity, MessageEntityMention):
        base["type"] = "mention"
    if isinstance(entity, MessageEntityHashtag):
        base["type"] = "hashtag"
    if isinstance(entity, MessageEntityUrl):
        base["type"] = "url"
    if isinstance(entity, MessageEntityBold):
        base["type"] = "bold"
    if isinstance(entity, MessageEntityItalic):
        base["type"] = "italic"
    if isinstance(entity, MessageEntityCode):
        base["type"] = "code"
    if isinstance(entity, MessageEntityPhone):
        base["type"] = "phone"
    return base


def serialize_message(msg) -> dict:
    """Convert a Telegram Message to a JSON-serializable dict."""
    return {
        "id": msg.id,
        "date": msg.date.isoformat() if msg.date else None,
        "text": msg.text or "",
        "raw_text": msg.raw_text or "",
        "entities": [serialize_entity(e) for e in (msg.entities or [])],
        "views": msg.views,
        "forwards": msg.forwards,
        "media_type": type(msg.media).__name__ if msg.media else None,
        "reply_to_msg_id": msg.reply_to.reply_to_msg_id if msg.reply_to else None,
        "grouped_id": msg.grouped_id,
    }


# ---------------------------------------------------------------------------
# Fetching
# ---------------------------------------------------------------------------


async def fetch_channel(client: TelegramClient, channel_username: str) -> list[dict]:
    """Fetch recent messages from a single channel."""
    try:
        entity = await client.get_entity(channel_username)
    except Exception as e:
        print(f"  ERROR resolving @{channel_username}: {e}")
        return []

    messages = []
    async for msg in client.iter_messages(entity, limit=MESSAGES_PER_CHANNEL):
        if msg.text:  # skip media-only posts for now
            messages.append(serialize_message(msg))

    return messages


async def main():
    load_dotenv(ENV_PATH)

    api_id = os.getenv("TELETHON_API_ID")
    api_hash = os.getenv("TELETHON_API_HASH")
    session = os.getenv("TELETHON_SESSION")

    if not api_id or not api_hash:
        print("ERROR: TELETHON_API_ID and TELETHON_API_HASH must be set in .env")
        sys.exit(1)

    if not session:
        print("ERROR: TELETHON_SESSION must be set in .env")
        print("Run 'uv run python scripts/generate_session.py' first to generate it.")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    client = TelegramClient(StringSession(session), int(api_id), api_hash)

    print("Connecting to Telegram...")
    await client.connect()
    if not await client.is_user_authorized():
        print("ERROR: Session is invalid or expired. Regenerate with generate_session.py")
        sys.exit(1)
    print("Connected!\n")

    summary = {}

    for channel in CHANNELS:
        print(f"Fetching @{channel}...")
        messages = await fetch_channel(client, channel)

        output_path = OUTPUT_DIR / f"{channel}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)

        summary[channel] = len(messages)
        print(f"  Saved {len(messages)} messages -> {output_path}")

    await client.disconnect()

    # Print summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    total = 0
    for channel, count in summary.items():
        print(f"  @{channel:25s} {count:3d} messages")
        total += count
    print(f"  {'TOTAL':25s} {total:3d} messages")
    print(f"\nRaw JSON saved to: {OUTPUT_DIR}")
    print(f"Timestamp: {datetime.now().isoformat()}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    asyncio.run(main())
