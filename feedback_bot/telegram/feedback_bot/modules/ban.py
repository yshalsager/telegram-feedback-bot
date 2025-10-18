"""Ban management commands for feedback bots."""

from __future__ import annotations

from django.utils.translation import gettext as _
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from feedback_bot.crud import (
    ensure_user_ban,
    get_owner_message_mapping,
    lift_user_ban,
    list_banned_users,
)

MISSING_TARGET_MESSAGE = _('Reply to a forwarded message or pass a numeric user ID.')


def _is_owner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    return (
        update.effective_user is not None
        and update.effective_user.id == context.bot_data['bot_config'].owner_id
    )


async def _resolve_target_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int | None:
    message = update.effective_message
    if message is None:
        return None

    bot_config = context.bot_data['bot_config']

    if message.reply_to_message:
        mapping = await get_owner_message_mapping(bot_config, message.reply_to_message.message_id)
        if mapping is not None:
            return mapping.user_chat.user_telegram_id

    if context.args:
        try:
            return int(context.args[0])
        except (TypeError, ValueError):
            return None

    return None


async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_owner(update, context):
        return

    target_user_id = await _resolve_target_user(update, context)
    if target_user_id is None:
        await update.effective_message.reply_text(MISSING_TARGET_MESSAGE)
        return

    banned_user, created = await ensure_user_ban(context.bot_data['bot_config'].id, target_user_id)
    text = (
        _('User %(user_id)d banned.') if created else _('User %(user_id)d was already banned.')
    ) % {'user_id': banned_user.user_telegram_id}
    await update.effective_message.reply_text(text)


async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_owner(update, context):
        return

    target_user_id = await _resolve_target_user(update, context)
    if target_user_id is None:
        await update.effective_message.reply_text(MISSING_TARGET_MESSAGE)
        return

    removed = await lift_user_ban(context.bot_data['bot_config'].id, target_user_id)
    text = (
        _('User %(user_id)d unbanned.') if removed else _('User %(user_id)d was not banned.')
    ) % {'user_id': target_user_id}
    await update.effective_message.reply_text(text)


async def list_bans(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_owner(update, context):
        return

    banned_users = await list_banned_users(context.bot_data['bot_config'].id)
    if not banned_users:
        await update.effective_message.reply_text(_('No banned users.'))
        return

    entries = '\n'.join(str(user.user_telegram_id) for user in banned_users)
    await update.effective_message.reply_text(
        _('Banned users:\n%(entries)s') % {'entries': entries}
    )


HANDLERS = [
    CommandHandler('ban', ban_user),
    CommandHandler('unban', unban_user),
    CommandHandler('banned', list_bans),
]
