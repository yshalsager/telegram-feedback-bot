"""
broadcast module.
"""
import logging
from asyncio import sleep

from telegram import Message, Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes, filters

from feedbackbot import SLEEP_AFTER_SEND
from feedbackbot.db.curd import get_all_chats
from feedbackbot.utils.filters import FilterBotAdmin
from feedbackbot.utils.telegram_handlers import command_handler, tg_exceptions_handler

logger = logging.getLogger(__name__)


@command_handler("broadcast", filters=filters.REPLY & FilterBotAdmin())
@tg_exceptions_handler
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Broadcasts message to bot users."""
    assert update.effective_chat is not None
    assert update.effective_message is not None
    message_to_send: Message | None = update.effective_message.reply_to_message
    assert message_to_send is not None
    failed_to_send = 0
    sent_successfully = 0
    chats = get_all_chats()
    for chat in chats:
        try:
            await context.bot.copy_message(
                chat_id=chat.user_id,
                from_chat_id=message_to_send.chat.id,
                message_id=message_to_send.message_id,
            )
            sent_successfully += 1
            await sleep(SLEEP_AFTER_SEND)
        except TelegramError as err:
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
    await update.effective_message.reply_text(
        broadcast_status_message,
        reply_to_message_id=update.effective_message.message_id,
    )
