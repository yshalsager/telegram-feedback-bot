"""
broadcast module.
"""

from pyrogram import Client, filters
from pyrogram.types import Message

from src.bot.db.crud import get_all_chats
from src.bot.db.session import session_scope
from src.bot.utils.filters import is_admin
from src.common.utils.telegram import broadcast_messages
from src.common.utils.telegram_handlers import tg_exceptions_handler


@Client.on_message(filters.command('broadcast') & filters.reply & is_admin)
@tg_exceptions_handler
async def broadcast(client: Client, message: Message) -> None:
    """Broadcasts message to bot users."""
    message_to_send: Message | None = message.reply_to_message
    assert message_to_send is not None
    with session_scope(client.me.id) as session:
        broadcast_status_message = await broadcast_messages(
            [chat.user_id for chat in get_all_chats(session)], message_to_send
        )
        await message.reply_text(
            broadcast_status_message,
            reply_to_message_id=message.reply_to_message_id,
        )
