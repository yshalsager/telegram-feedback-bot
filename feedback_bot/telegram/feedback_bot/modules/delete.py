"""Delete command for feedback bots."""

from __future__ import annotations

from django.utils.translation import gettext as _
from telegram import Update
from telegram.error import BadRequest, Forbidden
from telegram.ext import CommandHandler, ContextTypes

from feedback_bot.crud import (
    delete_message_mapping,
    delete_message_mappings,
    get_owner_message_mapping,
    list_chat_message_mappings,
)


async def _delete_message(
    context: ContextTypes.DEFAULT_TYPE, chat_id: int | None, message_id: int | None
) -> bool:
    if context.bot is None or chat_id is None or message_id is None:
        return False

    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        return True
    except BadRequest as exc:
        payload = exc.message.lower()
        return bool('message to delete not found' in payload or 'message not found' in payload)
    except Forbidden as exc:
        payload = exc.message.lower()
        return bool('user is deactivated' in payload or 'bot was blocked by the user' in payload)


async def delete_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if (
        message is None
        or update.effective_user is None
        or message.reply_to_message is None
        or context.bot is None
    ):
        return

    bot_config = context.bot_data['bot_config']
    if update.effective_user.id != bot_config.owner_id:
        return

    mapping = await get_owner_message_mapping(bot_config, message.reply_to_message.message_id)
    if mapping is None:
        await message.reply_text(_('Nothing to delete.'))
        return

    owner_chat_id = bot_config.forward_chat_id or bot_config.owner_id
    owner_deleted = await _delete_message(context, owner_chat_id, mapping.owner_message_id)
    user_deleted = await _delete_message(
        context,
        mapping.user_chat.user_telegram_id,
        mapping.user_message_id,
    )

    if owner_deleted or user_deleted:
        await delete_message_mapping(mapping)
        await _delete_message(context, message.chat_id, message.message_id)
        return

    await message.reply_text(_('Could not delete the message.'))


async def _delete_many(
    context: ContextTypes.DEFAULT_TYPE, chat_id: int | None, message_ids: list[int | None]
) -> bool:
    deleted_any = False
    for message_id in message_ids:
        if await _delete_message(context, chat_id, message_id):
            deleted_any = True
    return deleted_any


async def clear_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:  # noqa: PLR0911
    message = update.effective_message
    if (
        message is None
        or update.effective_user is None
        or message.reply_to_message is None
        or context.bot is None
    ):
        return

    bot_config = context.bot_data['bot_config']
    if update.effective_user.id != bot_config.owner_id:
        return

    mapping = await get_owner_message_mapping(bot_config, message.reply_to_message.message_id)
    if mapping is None:
        await message.reply_text(_('Nothing to clear.'))
        return

    feedback_chat = mapping.user_chat
    mappings = await list_chat_message_mappings(bot_config, feedback_chat)
    if not mappings:
        await message.reply_text(_('Nothing to clear.'))
        return

    start_index = 0
    for idx, entry in enumerate(mappings):
        if entry.owner_message_id == mapping.owner_message_id or entry.pk == mapping.pk:
            start_index = idx
            break
    else:
        await message.reply_text(_('Nothing to clear.'))
        return

    target_mappings = mappings[start_index:]
    if not target_mappings:
        await message.reply_text(_('Nothing to clear.'))
        return

    owner_chat_id = bot_config.forward_chat_id or bot_config.owner_id
    owner_deleted = await _delete_many(
        context,
        owner_chat_id,
        [entry.owner_message_id for entry in target_mappings],
    )
    user_deleted = await _delete_many(
        context,
        feedback_chat.user_telegram_id,
        [entry.user_message_id for entry in target_mappings],
    )

    if not (owner_deleted or user_deleted):
        await message.reply_text(_('Could not clear messages.'))
        return

    await delete_message_mappings(target_mappings)
    await _delete_message(context, message.chat_id, message.message_id)


HANDLERS = [
    CommandHandler('delete', delete_feedback),
    CommandHandler('clear', clear_feedback),
]
