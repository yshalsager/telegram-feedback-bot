from plate import Plate
from pyrogram import Client, filters
from pyrogram.types import Message

from src.bot.db.crud import (
    get_user_chat_of_message,
    get_user_id_of_topic,
    increment_outgoing_stats,
)
from src.bot.db.session import session_scope
from src.builder.db.crud import TBot, get_bot
from src.common.utils.i18n import localize
from src.common.utils.telegram_handlers import tg_exceptions_handler


@Client.on_message(
    filters.private & filters.reply & ~filters.regex(r'^/\w+$') & ~filters.me, group=-1
)
@Client.on_message(filters.group & ~filters.regex(r'^/\w+$'), group=-1)
@tg_exceptions_handler
@localize
async def replier(client: Client, message: Message, i18n: Plate) -> None:
    bot_id: int = client.me.id
    bot: TBot | None = get_bot(bot_id)
    if not bot:
        return
    if (message.chat.id == message.from_user.id and message.from_user.id != bot.owner) or (
        message.reply_to_message
        and not message.reply_to_message.forward_sender_name
        and message.reply_to_message.from_user.id == bot_id
        and message.from_user.id == bot.owner
    ):
        return
    with session_scope(bot_id) as session:
        user_id = (
            get_user_id_of_topic(session, message.message_thread_id)
            if bot.group and message.message_thread_id
            else get_user_chat_of_message(session, message.reply_to_message_id)
        )
        await message.copy(user_id if user_id != -1 else bot.owner)
        increment_outgoing_stats(session)
    await message.reply_text(
        bot.sent_message or i18n('default_sent'),
        reply_to_message_id=message.reply_to_message_id,
    )
