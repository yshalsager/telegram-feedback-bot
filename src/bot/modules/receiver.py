from plate import Plate
from pyrogram import Client, filters
from pyrogram.errors import TopicDeleted
from pyrogram.types import Message

from src.bot.db.crud import (
    add_mapping,
    get_topic,
    increment_incoming_stats,
    increment_usage_times,
    remove_user_mappings,
)
from src.bot.db.session import session_scope
from src.bot.utils.telegram import create_topic_and_add_to_db
from src.builder.db.crud import TBot, get_bot
from src.common.utils.i18n import localize
from src.common.utils.telegram_handlers import tg_exceptions_handler


@Client.on_message(filters.private & ~filters.regex(r'^/\w+$') & ~filters.me)
@tg_exceptions_handler
@localize
async def forwarder(client: Client, message: Message, i18n: Plate) -> None:
    bot: TBot | None = get_bot(client.me.id)
    if not bot:
        return
    chat_id: int = bot.group or bot.owner
    if message.chat.id == chat_id and message.from_user.id == bot.owner:
        message.continue_propagation()
    with session_scope(client.me.id) as session:
        topic_id = get_topic(session, message.chat.id)
        if topic_id == 0 and bot.group:
            topic = await create_topic_and_add_to_db(client, message, i18n, session, bot.group)
            topic_id = topic.topic_id if topic else 0
        try:
            forwarded: Message = await message.forward(
                chat_id=chat_id,
                message_thread_id=topic_id,
                disable_notification=True,
            )
        except TopicDeleted:
            remove_user_mappings(session, message.chat.id)
            topic = await create_topic_and_add_to_db(client, message, i18n, session, bot.group)
            topic_id = topic.topic_id if topic else 0
            forwarded = await message.forward(
                chat_id=chat_id,
                message_thread_id=topic_id,
                disable_notification=True,
            )
        add_mapping(
            session,
            message.chat.id,
            message.id,
            topic_id or 0,
            forwarded.id,
        )
        await message.reply_text(
            bot.received_message or i18n('default_received'),
            reply_to_message_id=message.id,
        )
        increment_incoming_stats(session)
        increment_usage_times(session, message.chat.id)
