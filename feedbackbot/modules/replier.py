from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from feedbackbot import TELEGRAM_CHAT_ID, application
from feedbackbot.db.curd import get_user_id_of_topic, increment_outgoing_stats


async def reply_handler(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_message is not None
    user_id = get_user_id_of_topic(update.effective_message.message_thread_id)
    await update.effective_message.copy(user_id)
    increment_outgoing_stats()


# TODO Message handler filters needs to be further tweaked to reply only on reply to a topic message
application.add_handler(
    MessageHandler(
        filters.IS_TOPIC_MESSAGE
        & filters.REPLY
        & filters.Chat(chat_id=int(TELEGRAM_CHAT_ID))
        & ~filters.COMMAND,
        reply_handler,
    )
)
