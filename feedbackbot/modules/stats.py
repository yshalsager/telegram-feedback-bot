""" Bot stats module"""
from telegram import Update
from telegram.ext import ContextTypes

from feedbackbot.db.curd import get_chats_count, get_stats
from feedbackbot.utils.filters import FilterBotAdmin
from feedbackbot.utils.telegram_handlers import (
    command_handler,
    tg_exceptions_handler,
)


@command_handler("stats", FilterBotAdmin())
@tg_exceptions_handler
async def stats_for_users_handler(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Show Bot stats for admins.
    :param update: `telegram.Update` of `python-telegram-bot`.
    :param _: `telegram.ext.CallbackContext` of `python-telegram-bot`.
    :return: None
    """
    assert update.effective_message is not None
    total_users_count: int = get_chats_count()
    messages_stats = get_stats()
    if messages_stats:
        incoming_count = messages_stats.incoming
        outgoing_count = messages_stats.outgoing
    else:
        incoming_count = outgoing_count = 0
    text_message = f"""📈 <b>إحصائيات البوت</b>

👥 <b>المستخدمون</b>
• {total_users_count} مستخدم للبوت

✍️ <b>الرسائل</b>
• {incoming_count} رسالة واردة
  {outgoing_count} رد على الرسائل
"""
    await update.effective_message.reply_html(text_message)
