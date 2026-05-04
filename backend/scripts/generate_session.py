"""
One-time script: Generate a Telethon StringSession.

Run this on a machine where the side account can receive Telegram codes.
The code will appear as a message from Telegram in the app (NOT via SMS).

Usage:
    cd backend
    uv run python scripts/generate_session.py

After entering the code, it prints a session string.
Copy that string and add it to your .env as TELETHON_SESSION.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from telethon.sessions import StringSession
from telethon.sync import TelegramClient

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(ENV_PATH)

api_id = os.getenv("TELETHON_API_ID")
api_hash = os.getenv("TELETHON_API_HASH")

if not api_id or not api_hash:
    print("ERROR: TELETHON_API_ID and TELETHON_API_HASH must be set in .env")
    sys.exit(1)

print("=" * 50)
print("Telethon StringSession Generator")
print("=" * 50)
print()
print("You will be asked for your phone number.")
print("The verification code will appear as a message")
print("from 'Telegram' in the Telegram app on your phone.")
print("Make sure the side account is logged in on at least one device.")
print()

with TelegramClient(StringSession(), int(api_id), api_hash) as client:
    session_string = client.session.save()
    print()
    print("=" * 50)
    print("SUCCESS! Copy the session string below")
    print("and add it to your .env as:")
    print()
    print(f"TELETHON_SESSION={session_string}")
    print()
    print("=" * 50)
