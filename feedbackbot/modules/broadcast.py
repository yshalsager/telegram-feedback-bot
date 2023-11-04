"""
broadcast module.
"""
import logging
from asyncio import sleep

from pyrogram import Client, filters
from pyrogram.errors import FloodWait, RPCError
from pyrogram.types import Message

from feedbackbot.db.curd import get_all_chats
from feedbackbot.utils.filters import is_admin
from feedbackbot.utils.telegram_handlers import tg_exceptions_handler

logger = logging.getLogger(__name__)

SLEEP_AFTER_SEND = 0.035  # Limit is ~30 messages/second; core.telegram.org/bots/faq


@Client.on_message(filters.command("broadcast") & filters.reply & is_admin)
@tg_exceptions_handler
async def broadcast(_: Client, message: Message) -> None:
    """Broadcasts message to bot users."""
    message_to_send: Message | None = message.reply_to_message
    assert message_to_send is not None
    failed_to_send = 0
    sent_successfully = 0
    chats = get_all_chats()
    for chat in chats:
        try:
            await message_to_send.copy(chat_id=chat.user_id)
            sent_successfully += 1
            await sleep(SLEEP_AFTER_SEND)
        except FloodWait as err:
            await sleep(err.value + 1)
            await message_to_send.copy(chat_id=chat.user_id)
            sent_successfully += 1
            await sleep(SLEEP_AFTER_SEND)
        except RPCError as err:
            failed_to_send += 1
            logger.warning(f"فشل إرسال الرسالة إلى {chat}:\n{err}")
    broadcast_status_message: str = (
        f"اكتمل النشر! أرسلت الرسالة إلى {sent_successfully} مستخدم ومجموعة\n"
    )
    if failed_to_send:
        broadcast_status_message += (
            f" فشل الإرسال إلى {failed_to_send}"
            f"مستخدمين/مجموعات، غالبا بسبب أن البوت طرد أو أوقف."
        )
    await message.reply_text(
        broadcast_status_message,
        reply_to_message_id=message.reply_to_message_id,
    )
