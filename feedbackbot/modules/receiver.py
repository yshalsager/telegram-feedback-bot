from os import getenv

from telegram import Message, Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes, MessageHandler, filters
from telegram.helpers import escape_markdown

from feedbackbot import TELEGRAM_CHAT_ID, application
from feedbackbot.db.curd import (
    add_mapping,
    get_topic,
    increment_incoming_stats,
    increment_usage_times,
    remove_user_mappings,
)
from feedbackbot.utils.telegram import create_topic_and_add_to_db, get_reply_to_message_id

default_message_text = "استلمنا رسالتك. سنرد عليك في أقرب وقت."
message_text = escape_markdown(
    getenv("MESSAGE_RECEIVED", default_message_text).replace("\\n", "\n")
)


async def forward_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_message is not None
    topic_id = get_topic(update.effective_chat.id)
    if not topic_id:
        topic = await create_topic_and_add_to_db(update, context)
        topic_id = topic.topic_id
    try:
        forwarded: Message = await update.effective_message.forward(
            chat_id=TELEGRAM_CHAT_ID,
            message_thread_id=topic_id,
            disable_notification=True,
        )
    except BadRequest as err:
        if err.message == "Message thread not found":
            # Topic was deleted, create a new one
            remove_user_mappings(update.effective_chat.id)
            topic = await create_topic_and_add_to_db(update, context)
            topic_id = topic.topic_id
            forwarded = await update.effective_message.forward(
                chat_id=TELEGRAM_CHAT_ID,
                message_thread_id=topic_id,
                disable_notification=True,
            )
        else:
            raise err
    add_mapping(
        update.effective_chat.id,
        update.effective_message.message_id,
        topic_id,
        forwarded.message_id,
    )
    await update.effective_message.reply_text(
        message_text, reply_to_message_id=get_reply_to_message_id(update)
    )
    increment_incoming_stats()
    increment_usage_times(update.effective_chat.id)


application.add_handler(
    MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, forward_handler)
)
