import html
import json
import logging
import traceback

import regex as re
from pyrogram import Client
from pyrogram.types import Message

from src import BOT_TOKEN, BOTS, IS_DEBUG, LOG_TOPIC_ID, TELEGRAM_CHAT_ID
from src.builder.db.crud import get_bot
from src.common.utils.telegram import get_bot_id

logger = logging.getLogger(__name__)


def split_string(string: str, n: int) -> list[str]:
    return [string[i : i + n] for i in range(0, len(string), n)]


async def error_handler(exception: Exception, client: Client, update: Message | None) -> None:
    """Log the error and send a telegram message to notify the developer."""
    logger.error('Exception while handling an update:', exc_info=exception)
    if not IS_DEBUG and not LOG_TOPIC_ID:
        return
    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    traceback_str = html.escape(
        re.sub(
            r'File \"(.*site-packages)',
            '<pkgs>',
            ''.join(traceback.format_exception(None, exception, exception.__traceback__)),
        )
    )
    # Build the message with some markup and additional information about what happened.
    message = (
        f'An exception was raised while handling an update\n'
        f"<pre language='json'>{html.escape(json.dumps(json.loads(str(update)), indent=1, ensure_ascii=False))}"
        '</pre>'
    )
    main_bot = BOTS[get_bot_id(BOT_TOKEN)]
    sent = await main_bot.send_message(
        chat_id=TELEGRAM_CHAT_ID, message_thread_id=int(LOG_TOPIC_ID), text=message
    )
    for split_traceback in split_string(traceback_str, 4000):
        await main_bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            message_thread_id=int(LOG_TOPIC_ID),
            text=f'<pre language="python">{get_bot(get_bot_id(client.bot_token))!s}\n{split_traceback}</pre>',
            reply_to_message_id=sent.id,
        )
