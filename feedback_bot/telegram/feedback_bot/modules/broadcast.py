"""Broadcast command for feedback bots."""

from functools import partial
from typing import Any

from django.utils.translation import gettext_lazy as _
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, filters

from feedback_bot.crud import get_feedback_chat_targets, record_broadcast_message
from feedback_bot.telegram.utils.broadcast import broadcast_to_chats


def _resolve_bot_reference(bot_config: Any) -> Any:
    if hasattr(bot_config, 'feedback_chats'):
        return bot_config
    if hasattr(bot_config, 'id') and bot_config.id is not None:  # type: ignore[attr-defined]
        return bot_config.id  # type: ignore[attr-defined]
    if hasattr(bot_config, 'pk') and bot_config.pk is not None:  # type: ignore[attr-defined]
        return bot_config.pk  # type: ignore[attr-defined]
    return None


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Broadcasts message to feedback bot users."""
    if (
        update.effective_message is None
        or update.effective_message.reply_to_message is None
        or update.effective_user is None
        or context.bot is None
    ):
        return

    bot_config = context.bot_data['bot_config']

    owner_id = getattr(bot_config, 'owner_id', None)
    if owner_id is None or update.effective_user.id != owner_id:
        return

    bot_reference = _resolve_bot_reference(bot_config)
    if bot_reference is None:
        return

    chat_ids = await get_feedback_chat_targets(bot_reference)
    if not chat_ids:
        await update.effective_message.reply_text(
            _('No subscribers to broadcast to.'),
            reply_to_message_id=update.effective_message.message_id,
        )
        return

    message_to_send = update.effective_message.reply_to_message
    sent, failed = await broadcast_to_chats(
        context.bot,
        message_to_send,
        chat_ids,
        record=partial(record_broadcast_message, bot=bot_reference),
    )
    status = _('Broadcast completed: sent to %(sent)d chats.') % {'sent': sent}
    if failed:
        status += _(' Failed for %(failed)d chats.') % {'failed': failed}

    await update.effective_message.reply_text(
        status,
        reply_to_message_id=update.effective_message.message_id,
    )


HANDLERS = [
    CommandHandler('broadcast', broadcast, filters=filters.REPLY),
]
