"""Group management handlers for feedback bots."""

from django.utils.translation import gettext_lazy as _
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from feedback_bot.crud import update_bot_forward_chat_by_telegram_id


async def link_bot_to_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set the chat as the feedback destination when the bot joins a group."""
    if (
        update.effective_message is None
        or not update.effective_message.new_chat_members
        or context.bot is None
        or context.bot.id is None
        or update.effective_chat is None
        or not any(
            member.id == context.bot.id for member in update.effective_message.new_chat_members
        )
        or getattr(context.bot_data.get('bot_config', None), 'forward_chat_id', None)
        == update.effective_chat.id
    ):
        return

    is_linked = await update_bot_forward_chat_by_telegram_id(
        context.bot.id, update.effective_chat.id
    )
    if not is_linked:
        return

    await update.effective_message.reply_text(
        _('%(bot_name)s will forward feedback to %(chat_name)s.')
        % {
            'bot_name': context.bot.first_name or context.bot.username or 'bot',
            'chat_name': (
                update.effective_chat.title
                or update.effective_chat.username
                or update.effective_chat.full_name
                or str(update.effective_chat.id)
            ),
        }
    )


async def unlink_bot_from_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clear the forwarding chat when the bot leaves the linked group and send a notification to the owner."""
    if (
        update.effective_message is None
        or context.bot is None
        or context.bot.id is None
        or update.effective_chat is None
        or update.effective_message.left_chat_member is None
        or update.effective_message.left_chat_member.id != context.bot.id
    ):
        return

    bot_config = context.bot_data.get('bot_config')
    if getattr(bot_config, 'forward_chat_id', None) != update.effective_chat.id:
        return

    is_cleared = await update_bot_forward_chat_by_telegram_id(context.bot.id, None)
    if not is_cleared:
        return

    await context.bot.send_message(
        bot_config.owner_id,
        _('%(bot_name)s has been unlinked from %(chat_title)s.')
        % {
            'bot_name': context.bot.first_name,
            'chat_title': update.effective_chat.title,
        },
    )


HANDLERS = [
    MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS & filters.ChatType.GROUPS, link_bot_to_group
    ),
    MessageHandler(
        filters.StatusUpdate.LEFT_CHAT_MEMBER & filters.ChatType.GROUPS, unlink_bot_from_group
    ),
]
