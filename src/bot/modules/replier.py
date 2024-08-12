from plate import Plate
from pyrogram import Client, filters
from pyrogram.types import Message

from src.bot.db.crud import (
    add_mapping,
    get_mapping,
    increment_outgoing_stats,
)
from src.bot.db.session import session_scope
from src.bot.utils.telegram import get_media
from src.builder.db.crud import get_bot
from src.builder.db.models.bot import Bot
from src.common.utils.i18n import localize
from src.common.utils.telegram_handlers import tg_exceptions_handler


def should_process_reply(bot: Bot, client: Client, message: Message) -> bool:
    is_private_chat = message.chat.id == message.from_user.id
    is_not_owner = message.from_user.id != bot.owner
    is_reply_to_bot = (
        message.reply_to_message and message.reply_to_message.from_user.id == client.me.id
    )
    return not (is_private_chat and is_not_owner) and is_reply_to_bot


@Client.on_message(
    (filters.private | filters.group) & filters.reply & ~filters.regex(r'^/\w+$') & ~filters.me,
    group=-1,
)
@tg_exceptions_handler
@localize
async def replier(client: Client, message: Message, i18n: Plate) -> None:
    bot: Bot | None = get_bot(client.me.id)
    assert bot is not None
    if not should_process_reply(bot, client, message):
        return
    with session_scope(client.me.id) as session:
        mapping = get_mapping(session, destination=message.reply_to_message_id)
        if not mapping:
            return
        copied_message = await message.copy(mapping.user_id)
        add_mapping(
            session,
            mapping.user_id,
            copied_message.id,
            0,
            message.reply_to_message.id,
            outgoing=True,
        )
        increment_outgoing_stats(session)
    if bot.bot_settings.confirmations:
        await message.reply_text(
            bot.bot_settings.sent_message or i18n('default_sent'),
            reply_to_message_id=message.reply_to_message_id,
        )


@Client.on_edited_message(
    (filters.private | filters.group) & filters.reply & ~filters.regex(r'^/\w+$') & ~filters.me,
    group=-1,
)
@tg_exceptions_handler
@localize
async def edit_replier(client: Client, message: Message, i18n: Plate) -> None:
    bot: Bot | None = get_bot(client.me.id)
    assert bot is not None
    if not should_process_reply(bot, client, message):
        return
    with session_scope(client.me.id) as session:
        mapping = get_mapping(session, destination=message.reply_to_message.id, outgoing=True)
        if not mapping:
            return
        if message.media:
            media = get_media(message)
            if not media:
                return
            await client.edit_message_media(
                chat_id=mapping.user_id, message_id=mapping.source, media=media
            )
        elif message.text:
            await client.edit_message_text(
                chat_id=mapping.user_id, message_id=mapping.source, text=message.text
            )
        else:
            return
        if bot.bot_settings.confirmations:
            await message.reply_text(i18n('message_edited'), reply_to_message_id=message.id)
