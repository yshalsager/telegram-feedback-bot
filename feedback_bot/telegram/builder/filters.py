from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any

from django.conf import settings
from telegram import Message, MessageOriginHiddenUser, MessageOriginUser, Update
from telegram.ext import CallbackContext
from telegram.ext.filters import MessageFilter

from feedback_bot.crud import get_whitelist_users


async def is_whitelisted_user(message: Message) -> bool:
    return (
        message.from_user.id in settings.TELEGRAM_BUILDER_BOT_ADMINS
        or message.from_user.id in await get_whitelist_users()
    )


def whitelisted_only(
    func: Callable[[Update, CallbackContext], Awaitable[Any]],
) -> Callable[[Update, CallbackContext], Awaitable[Any]]:
    @wraps(func)
    async def wrapper(update: Update, context: CallbackContext, *args: Any, **kwargs: Any) -> Any:
        if not await is_whitelisted_user(update.message):
            return None
        return await func(update, context, *args, **kwargs)

    return wrapper


class IsAdmin(MessageFilter):
    def filter(self, message: Message) -> bool:
        return message.from_user.id in settings.TELEGRAM_BUILDER_BOT_ADMINS


class IsReplyToForwardedMessage(MessageFilter):
    def filter(self, message: Message) -> bool:
        """Check if this message is a reply to a forwarded message from a user"""
        if not message.reply_to_message:
            return False
        if not message.reply_to_message.forward_origin:
            return False
        # Only allow forwarded messages from users (known or hidden)
        return isinstance(
            message.reply_to_message.forward_origin, MessageOriginUser | MessageOriginHiddenUser
        )


is_admin = IsAdmin()
is_reply_to_forwarded_message = IsReplyToForwardedMessage()
