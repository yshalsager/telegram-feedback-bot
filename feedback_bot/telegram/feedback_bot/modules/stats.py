"""Stats command for feedback bots."""

from __future__ import annotations

from django.utils.translation import gettext as _
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from feedback_bot.crud import ensure_bot_stats, get_feedback_chat_count


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    user = update.effective_user
    bot_config = context.bot_data.get('bot_config') if context.bot_data else None

    if message is None or user is None or bot_config is None or user.id != bot_config.owner_id:
        return

    total_users = await get_feedback_chat_count(bot_config)
    stats_obj = await ensure_bot_stats(bot_config)

    text = _(
        '📈 <b>Bot statistics</b>\n\n'
        '👥 <b>Users</b>\n'
        '• %(users)d subscribers\n\n'
        '✍️ <b>Messages</b>\n'
        '• %(incoming)d inbound messages\n'
        '• %(outgoing)d replies sent\n'
    ) % {
        'users': total_users,
        'incoming': stats_obj.incoming_messages,
        'outgoing': stats_obj.outgoing_messages,
    }

    await message.reply_html(text)


HANDLERS = [
    CommandHandler('stats', stats),
]
