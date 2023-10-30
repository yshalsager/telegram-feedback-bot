import logging
from html import escape
from os import getenv

from telegram import Update
from telegram.ext import ContextTypes

from feedbackbot.utils.analytics import add_new_chat_to_db
from feedbackbot.utils.telegram import get_reply_to_message_id
from feedbackbot.utils.telegram_handlers import (
    command_handler,
    tg_exceptions_handler,
)

logger = logging.getLogger(__name__)

message_text = getenv("MESSAGE_START", "")


def get_default_message_text(chat_title: str) -> str:
    return f"مرحبا بك <b>{escape(chat_title)}</b>\nاترك رسالتك وسنجيبك في أسرع وقت\n"


@command_handler("start")
@command_handler("help")
@add_new_chat_to_db
@tg_exceptions_handler
async def start_handler(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_message is not None
    chat_title = update.effective_chat.full_name or update.effective_chat.title
    await update.effective_message.reply_html(
        message_text or get_default_message_text(chat_title),
        reply_to_message_id=get_reply_to_message_id(update),
    )
