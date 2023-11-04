from pyrogram import Client
from pyrogram.enums import ChatType
from pyrogram.types import Message

from feedbackbot import TELEGRAM_CHAT_ID
from feedbackbot.db.curd import add_topic
from feedbackbot.db.models.topic import Topic

CHAT_TYPES = {ChatType.PRIVATE: 0, ChatType.GROUP: 1, ChatType.SUPERGROUP: 1, ChatType.CHANNEL: 2}


def get_chat_type(message: Message) -> int:
    return CHAT_TYPES[message.chat.type]


def get_chat_title(message: Message) -> str:
    return message.chat.title or message.chat.full_name or ""


async def create_topic_and_add_to_db(client: Client, message: Message) -> Topic:
    chat_title = get_chat_title(message)
    forum_topic = await client.create_forum_topic(chat_id=TELEGRAM_CHAT_ID, title=chat_title)
    await client.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        message_thread_id=forum_topic.id,
        text=chat_title,
    )
    return add_topic(message.chat.id, forum_topic.id)
