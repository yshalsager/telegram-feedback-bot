from os import getenv

from pyrogram import Client, filters
from pyrogram.errors import BadRequest
from pyrogram.types import Message

from feedbackbot import TELEGRAM_CHAT_ID, app
from feedbackbot.db.curd import (
    add_mapping,
    get_topic,
    increment_incoming_stats,
    increment_usage_times,
    remove_user_mappings,
)
from feedbackbot.utils.telegram import create_topic_and_add_to_db

default_message_text = "استلمنا رسالتك. سنرد عليك في أقرب وقت."
message_text = getenv("MESSAGE_RECEIVED", default_message_text).replace("\\n", "\n")


@app.on_message(filters.private & ~filters.regex(r"^/\w+$"))
async def forward_handler(client: Client, message: Message) -> None:
    topic_id = get_topic(message.chat.id)
    if not topic_id:
        topic = await create_topic_and_add_to_db(client, message)
        topic_id = topic.topic_id
    try:
        forwarded: Message = await message.forward(
            chat_id=TELEGRAM_CHAT_ID,
            message_thread_id=topic_id,
            disable_notification=True,
        )
    except BadRequest as err:
        if err.value == "Message thread not found":
            # Topic was deleted, create a new one
            remove_user_mappings(message.chat.id)
            topic = await create_topic_and_add_to_db(client, message)
            topic_id = topic.topic_id
            forwarded = await message.forward(
                chat_id=TELEGRAM_CHAT_ID,
                message_thread_id=topic_id,
                disable_notification=True,
            )
        else:
            raise err
    add_mapping(
        message.chat.id,
        message.id,
        topic_id,
        forwarded.id,
    )
    await message.reply_text(message_text, reply_to_message_id=message.reply_to_message_id)
    increment_incoming_stats()
    increment_usage_times(message.chat.id)
