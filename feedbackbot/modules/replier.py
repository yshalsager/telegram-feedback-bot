from os import getenv

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from telegram.helpers import escape_markdown

from feedbackbot import TELEGRAM_CHAT_ID, application
from feedbackbot.db.curd import get_user_id_of_topic, increment_outgoing_stats
from feedbackbot.utils.filters import FilterTopicMessageReply
from feedbackbot.utils.telegram import get_reply_to_message_id

default_message_text = "رد على الرسالة بنجاح."
message_text = escape_markdown(
    getenv("MESSAGE_RECEIVED", default_message_text).replace("\\n", "\n")
)


async def reply_handler(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_message is not None
    user_id = get_user_id_of_topic(update.effective_message.message_thread_id)
    await update.effective_message.copy(user_id)
    increment_outgoing_stats()
    await update.effective_message.reply_text(
        message_text, reply_to_message_id=get_reply_to_message_id(update)
    )


application.add_handler(
    MessageHandler(
        FilterTopicMessageReply() & filters.Chat(chat_id=int(TELEGRAM_CHAT_ID)) & ~filters.COMMAND,
        reply_handler,
    )
)
