from plate import Plate
from pyrogram import Client
from pyrogram.enums import ChatType
from pyrogram.errors import ChatWriteForbidden
from pyrogram.types import Message
from sqlalchemy.orm import Session, scoped_session

from common.utils.i18n import localize
from src import TELEGRAM_CHAT_ID
from src.bot.db.crud import add_topic
from src.bot.db.models.topic import Topic

CHAT_TYPES = {ChatType.PRIVATE: 0, ChatType.GROUP: 1, ChatType.SUPERGROUP: 1, ChatType.CHANNEL: 2}


def get_chat_type(message: Message) -> int:
    return CHAT_TYPES[message.chat.type]


def get_chat_title(message: Message) -> str:
    return message.chat.title or message.chat.full_name or ''


@localize
async def create_topic_and_add_to_db(
    client: Client, message: Message, i18n: Plate, session: scoped_session[Session]
) -> Topic | None:
    chat_title = get_chat_title(message)
    try:
        forum_topic = await client.create_forum_topic(chat_id=TELEGRAM_CHAT_ID, title=chat_title)
        await client.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            message_thread_id=forum_topic.id,
            text=chat_title,
        )
        return add_topic(session, message.chat.id, forum_topic.id)
    except ChatWriteForbidden as err:
        if 'CreateForumTopic' in str(err):
            await client.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=i18n('create_forum_topic_error'),
            )
            return None
        raise err
