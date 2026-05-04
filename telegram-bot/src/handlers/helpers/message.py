import asyncio
import logging

from aiogram.types import CallbackQuery, LinkPreviewOptions, Message, ReplyKeyboardRemove

logger = logging.getLogger(__name__)


async def safe_callback_answer(callback: CallbackQuery, text: str | None = None) -> None:
    """
    Safely answer a callback query, handling expired callbacks gracefully.

    Args:
        callback: The callback query to answer
        text: Optional text to show to user (default: None)
    """
    try:
        await callback.answer(text=text)
    except Exception as e:
        if "query is too old" in str(e) or "response timeout expired" in str(e):
            # Callback expired, log but don't crash
            logger.warning("Callback expired for user %s: %s", callback.from_user.id, str(e))
        else:
            # Other error, log it
            logger.error("Error answering callback for user %s: %s", callback.from_user.id, str(e))


async def safe_edit_message(msg: Message, text: str, **kwargs) -> Message:
    """Safely edit a message, falling back to sending a new message if editing fails.

    Returns:
        Message: The edited message if successful, or the new message if fallback is used
    """
    try:
        link_preview = kwargs.get("link_preview")
        if not link_preview:
            link_preview = LinkPreviewOptions(is_disabled=True)
            await msg.edit_text(text, link_preview_options=link_preview, **kwargs)
        else:
            await msg.edit_text(text, **kwargs)
        return msg
    except Exception as edit_error:
        logger.warning("Failed to edit message, sending new message instead: %s", str(edit_error))
        # Try to send a new message to the same chat
        try:
            new_msg = await msg.bot.send_message(msg.chat.id, text, **kwargs)
            return new_msg
        except Exception as send_error:
            logger.error("Failed to send new message as fallback: %s", str(send_error))
            # Return original message as last resort
            return msg


async def dismiss_reply_keyboard(message: Message, emoji: str = "🏠") -> None:
    """Dismiss any active reply keyboard by sending and deleting a temporary message."""
    try:
        dismiss = await message.answer(f"{emoji}.", reply_markup=ReplyKeyboardRemove())
        await asyncio.sleep(0.3)
        await dismiss.delete()
    except Exception:
        logger.debug("Could not dismiss reply keyboard for chat %s", message.chat.id)


async def animate_dots(message: Message, base_text: str) -> None:
    """Cycle base_text + '.' / '..' / '...' every 0.8s until cancelled."""
    dots = [".", "..", "..."]
    i = 0
    while True:
        try:
            await message.edit_text(f"{base_text}{dots[i % 3]}")
        except Exception:
            pass
        i += 1
        await asyncio.sleep(0.8)


async def safe_edit_reply_markup(msg: Message, reply_markup=None) -> None:
    """Safely edit reply markup, silently handling errors when message is not modified.

    This handles the case where Telegram returns an error because the new reply markup
    is exactly the same as the current one.
    """
    try:
        await msg.edit_reply_markup(reply_markup=reply_markup)
    except Exception as e:
        # Check if it's the "message is not modified" error
        if "message is not modified" in str(e) or "Bad Request" in str(e):
            logger.debug("Reply markup not modified for message (already has same markup): %s", str(e))
        else:
            logger.warning("Failed to edit reply markup: %s", str(e))
