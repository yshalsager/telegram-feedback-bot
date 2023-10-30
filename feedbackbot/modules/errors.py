import html
import json
import logging
import traceback

import regex as re
from sqlalchemy.orm.exc import DetachedInstanceError
from telegram import Update
from telegram.constants import ParseMode
from telegram.error import NetworkError
from telegram.ext import ContextTypes

from feedbackbot import IS_DEBUG, TELEGRAM_CHAT_ID, TELEGRAM_LOG_TOPIC_ID, application
from feedbackbot.db.session import session

logger = logging.getLogger(__name__)


def split_string(string: str, n: int) -> list[str]:
    return [string[i : i + n] for i in range(0, len(string), n)]


async def error_handler(update: Update | object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    assert context.error is not None
    if isinstance(context.error, DetachedInstanceError):
        session.rollback()
    logger.error("Exception while handling an update:", exc_info=context.error)
    if isinstance(context.error, NetworkError):
        if TELEGRAM_LOG_TOPIC_ID:
            await context.bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                message_thread_id=TELEGRAM_LOG_TOPIC_ID,
                text=traceback.format_exception(None, context.error, context.error.__traceback__)[
                    -1
                ],
            )
        return
    logger.error("Exception while handling an update:", exc_info=context.error)
    if not TELEGRAM_LOG_TOPIC_ID or IS_DEBUG:
        return
    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    traceback_str = html.escape(
        re.sub(
            r"File \"(.*site-packages)",
            "<pkgs>",
            "".join(traceback.format_exception(None, context.error, context.error.__traceback__)),
        )
    )
    # Build the message with some markup and additional information about what happened.
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f"An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        # f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        # f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
    )
    sent = await context.bot.send_message(
        chat_id=TELEGRAM_LOG_TOPIC_ID, text=message, parse_mode=ParseMode.HTML
    )
    for split_traceback in split_string(traceback_str, 4000):
        await context.bot.send_message(
            chat_id=TELEGRAM_LOG_TOPIC_ID,
            text=f"<pre>{split_traceback}</pre>",
            parse_mode=ParseMode.HTML,
            reply_to_message_id=sent.id,
        )
    # raise context.error


application.add_error_handler(error_handler)
