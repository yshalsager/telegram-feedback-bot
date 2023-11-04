import html
import json
import logging
import traceback

import regex as re
from pyrogram.types import Message

from feedbackbot import IS_DEBUG, TELEGRAM_CHAT_ID, TELEGRAM_LOG_TOPIC_ID, app

logger = logging.getLogger(__name__)


def split_string(string: str, n: int) -> list[str]:
    return [string[i : i + n] for i in range(0, len(string), n)]


async def error_handler(exception: Exception, update: Message | None) -> None:
    """Log the error and send a telegram message to notify the developer."""
    logger.error("Exception while handling an update:", exc_info=exception)
    if not TELEGRAM_LOG_TOPIC_ID or IS_DEBUG:
        return
    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    traceback_str = html.escape(
        re.sub(
            r"File \"(.*site-packages)",
            "<pkgs>",
            "".join(traceback.format_exception(None, exception, exception.__traceback__)),
        )
    )
    # Build the message with some markup and additional information about what happened.
    message = (
        f"An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(str(update), indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
    )
    sent = await app.send_message(
        chat_id=TELEGRAM_CHAT_ID, message_thread_id=TELEGRAM_LOG_TOPIC_ID, text=message
    )
    for split_traceback in split_string(traceback_str, 4000):
        await app.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            message_thread_id=TELEGRAM_LOG_TOPIC_ID,
            text=f"<pre>{split_traceback}</pre>",
            reply_to_message_id=sent.id,
        )
