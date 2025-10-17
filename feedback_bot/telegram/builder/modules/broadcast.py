"""Broadcast command for the builder bot."""

from functools import partial

from django.utils.translation import gettext_lazy as _
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, filters

from feedback_bot.crud import get_builder_broadcast_targets, record_broadcast_message
from feedback_bot.telegram.builder.filters import is_admin
from feedback_bot.telegram.utils.broadcast import broadcast_to_chats


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Broadcasts message to builder bot users."""
    if (
        update.effective_message is None
        or update.effective_message.reply_to_message is None
        or context.bot is None
    ):
        return

    message_to_send = update.effective_message.reply_to_message
    chat_ids = await get_builder_broadcast_targets()
    if not chat_ids:
        await update.effective_message.reply_text(
            _('No recipients to broadcast to.'),
            reply_to_message_id=update.effective_message.message_id,
        )
        return

    sent, failed = await broadcast_to_chats(
        context.bot,
        message_to_send,
        chat_ids,
        record=partial(record_broadcast_message, bot=None),
    )
    status = _('Broadcast completed: sent to %(sent)d chats.') % {'sent': sent}
    if failed:
        status += _(' Failed for %(failed)d chats.') % {'failed': failed}

    await update.effective_message.reply_text(
        status,
        reply_to_message_id=update.effective_message.message_id,
    )


HANDLERS = [
    CommandHandler('broadcast', broadcast, filters=is_admin & filters.REPLY),
]
