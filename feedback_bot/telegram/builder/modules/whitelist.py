"""Bot restart module"""

from django.utils.translation import gettext_lazy as _
from telegram import MessageOriginHiddenUser, Update, User
from telegram.ext import CommandHandler, ContextTypes
from telegram.ext.filters import Regex

from feedback_bot.crud import create_user
from feedback_bot.telegram.builder.filters import is_admin, is_reply_to_forwarded_message


async def whitelist_user_from_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Whitelist user from reply message"""
    assert update.effective_message is not None
    assert update.effective_message.reply_to_message.forward_origin is not None
    forward_origin = update.effective_message.reply_to_message.forward_origin
    if isinstance(forward_origin, MessageOriginHiddenUser):
        await update.message.reply_text(str(_('cant_whitelist_hidden_user')))
        return
    user: User = forward_origin.sender_user
    await create_user(user.to_dict())
    await update.message.reply_text(str(_('user_whitelisted')))


async def whitelist_user_from_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Whitelist user from id"""
    assert update.effective_message is not None
    assert context.matches is not None
    user_id = int(context.matches[0].group(1))
    await create_user({'id': user_id})
    await update.message.reply_text(str(_('user_whitelisted')))


HANDLERS = [
    CommandHandler('whitelist', whitelist_user_from_id, is_admin & Regex(r'^/whitelist\s+(\d+)$')),
    CommandHandler(
        'whitelist', whitelist_user_from_reply, is_admin & is_reply_to_forwarded_message
    ),
]
