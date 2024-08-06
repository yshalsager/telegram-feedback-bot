from plate import Plate
from pyrogram import Client, filters
from pyrogram.types import Message

from src.bot.db.crud import get_user_chat_of_message, increment_outgoing_stats
from src.bot.db.session import session_scope
from src.builder.db.crud import TBot, get_bot
from src.common.utils.i18n import localize
from src.common.utils.telegram_handlers import tg_exceptions_handler


@Client.on_message(
    (filters.private | filters.group) & filters.reply & ~filters.regex(r'^/\w+$') & ~filters.me,
    group=-1,
)
@tg_exceptions_handler
@localize
async def replier(client: Client, message: Message, i18n: Plate) -> None:
    bot: TBot | None = get_bot(client.me.id)
    assert bot is not None
    if (message.chat.id == message.from_user.id and message.from_user.id != bot.owner) or not (
        message.reply_to_message and message.reply_to_message.from_user.id == client.me.id
    ):
        return
    with session_scope(client.me.id) as session:
        user_id = get_user_chat_of_message(session, message.reply_to_message_id)
        if user_id == -1:
            return
        await message.copy(user_id)
        increment_outgoing_stats(session)
    await message.reply_text(
        bot.sent_message or i18n('default_sent'),
        reply_to_message_id=message.reply_to_message_id,
    )
