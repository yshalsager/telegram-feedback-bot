import logging
from html import escape
from os import getenv

from pyrogram import Client, filters
from pyrogram.types import Message

from feedbackbot.utils.analytics import add_new_chat_to_db
from feedbackbot.utils.telegram import get_chat_title
from feedbackbot.utils.telegram_handlers import tg_exceptions_handler

logger = logging.getLogger(__name__)

message_text = getenv("MESSAGE_START", "").replace("\\n", "\n")


def get_default_message_text(chat_title: str) -> str:
    return f"مرحبا بك <b>{escape(chat_title)}</b>\nاترك رسالتك وسنجيبك في أسرع وقت\n"


@Client.on_message(filters.command("start"))
@Client.on_message(filters.command("help"))
@add_new_chat_to_db
@tg_exceptions_handler
async def start_handler(_: Client, message: Message) -> None:
    await message.reply_text(
        message_text or get_default_message_text(get_chat_title(message)),
        reply_to_message_id=message.reply_to_message_id,
    )
