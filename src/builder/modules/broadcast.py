"""
broadcast module.
"""

from pyrogram import Client, filters
from pyrogram.types import Message

from src import BOT_ADMINS
from src.builder.db.crud import get_all_owners
from src.common.utils.filters import is_admin
from src.common.utils.telegram import broadcast_messages
from src.common.utils.telegram_handlers import tg_exceptions_handler


@Client.on_message(filters.command('broadcast') & filters.reply & is_admin(BOT_ADMINS))
@tg_exceptions_handler
async def broadcast(_: Client, message: Message) -> None:
    """Broadcasts message to bot users."""
    message_to_send: Message | None = message.reply_to_message
    assert message_to_send is not None
    broadcast_status_message = await broadcast_messages(
        [bot.owner for bot in get_all_owners()], message_to_send
    )
    await message.reply_text(
        broadcast_status_message,
        reply_to_message_id=message.reply_to_message_id,
    )
