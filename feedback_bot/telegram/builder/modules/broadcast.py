"""Broadcast command for the builder bot."""

from functools import partial

from django.utils.translation import gettext_lazy as _
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, filters

from feedback_bot.crud import get_builder_broadcast_targets, record_broadcast_message
from feedback_bot.telegram.builder.filters import is_admin
from feedback_bot.telegram.utils.broadcast import (
    broadcast_to_chats,
    extract_filters_text,
    filters_help_text,
    parse_broadcast_filters,
)


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if (
        update.effective_message is None
        or update.effective_message.reply_to_message is None
        or context.bot is None
    ):
        return

    filters_text = extract_filters_text(update.effective_message)
    filters_payload, error = parse_broadcast_filters(filters_text)
    if error:
        await update.effective_message.reply_text(f'{error}\n{filters_help_text()}')
        return

    chat_ids = await get_builder_broadcast_targets(filters_payload or None)
    if not chat_ids:
        await update.effective_message.reply_text(
            _('No recipients to broadcast to.'),
            reply_to_message_id=update.effective_message.message_id,
        )
        return

    source = update.effective_message.reply_to_message
    sent, failed = await broadcast_to_chats(
        context.bot,
        source,
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
