from plate import Plate
from pyrogram import Client, filters
from pyrogram.errors import TopicDeleted
from pyrogram.types import Message

from src.bot.db.crud import (
    add_mapping,
    get_mapping,
    get_topic,
    increment_incoming_stats,
    increment_usage_times,
    remove_user_mappings,
    update_mapping,
)
from src.bot.db.session import session_scope
from src.bot.utils.telegram import create_topic_and_add_to_db
from src.builder.db.crud import get_bot
from src.builder.db.models.bot import Bot
from src.common.utils.i18n import localize
from src.common.utils.telegram_handlers import tg_exceptions_handler


@Client.on_message(filters.private & ~filters.regex(r'^/\w+$') & ~filters.me)
@tg_exceptions_handler
@localize
async def forwarder(client: Client, message: Message, i18n: Plate) -> None:
    bot: Bot | None = get_bot(client.me.id)
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
            )
        except TopicDeleted:
            remove_user_mappings(session, message.chat.id)
            if bot.group:
                topic = await create_topic_and_add_to_db(client, message, i18n, session, bot.group)
                topic_id = topic.topic_id if topic else 0
            else:
                topic_id = 0
            forwarded = await message.forward(
                chat_id=chat_id,
                message_thread_id=topic_id,
            )
        add_mapping(
            session,
            message.chat.id,
            message.id,
            topic_id or 0,
            forwarded.id,
        )
        if bot.bot_settings.confirmations:
            await message.reply_text(
                bot.bot_settings.received_message or i18n('default_received'),
                reply_to_message_id=message.id,
            )
        increment_incoming_stats(session)
        increment_usage_times(session, message.chat.id)


@Client.on_edited_message(filters.private & ~filters.regex(r'^/\w+$') & ~filters.me)
@tg_exceptions_handler
@localize
async def edit_forwarder(client: Client, message: Message, i18n: Plate) -> None:
    bot: Bot | None = get_bot(client.me.id)
    if not bot:
        return
    with session_scope(client.me.id) as session:
        mapping = get_mapping(session, message.from_user.id, message.id)
        if not mapping:
            return
        chat_id = bot.group or bot.owner
        original_message = await client.get_messages(chat_id, mapping.destination)
        # await client.delete_messages(chat_id=chat_id, message_ids=mapping.destination)
        new_message = await message.forward(chat_id=chat_id, message_thread_id=mapping.topic_id)
        update_mapping(session, message.from_user.id, message.id, new_message.id)
        if bot.bot_settings.confirmations:
            await client.send_message(
                chat_id=chat_id,
                text=i18n(
                    'user_edited_message',
                    original_link=original_message.link,
                    edited_link=new_message.link,
                ),
                message_thread_id=mapping.topic_id,
                reply_to_message_id=original_message.id,
            )
