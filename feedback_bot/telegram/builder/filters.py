from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any

from django.conf import settings
from telegram import Message, Update
from telegram.ext import CallbackContext

from feedback_bot.telegram.builder.crud import get_whitelist_users


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
