from os import getenv

from pyrogram import Client, filters
from pyrogram.types import Message

from feedbackbot import TELEGRAM_CHAT_ID
from feedbackbot.db.curd import get_user_id_of_topic, increment_outgoing_stats
from feedbackbot.utils.filters import is_topic_reply

default_message_text = "رد على الرسالة بنجاح."
message_text = getenv("MESSAGE_RECEIVED", default_message_text).replace("\\n", "\n")


@Client.on_message(is_topic_reply & filters.chat(TELEGRAM_CHAT_ID) & ~filters.regex(r"^/\w+$"))
async def reply_handler(_: Client, message: Message) -> None:
    user_id = get_user_id_of_topic(message.message_thread_id)
    await message.copy(user_id)
    increment_outgoing_stats()
    await message.reply_text(message_text, reply_to_message_id=message.reply_to_message_id)
