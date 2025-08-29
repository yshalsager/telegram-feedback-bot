from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any

from django.conf import settings
from telegram import Message, Update

from feedback_bot.telegram.bot import CustomContext
from feedback_bot.telegram.builder.crud import get_whitelist_users


async def is_whitelisted_user(message: Message) -> bool:
    return (
        message.from_user.id in settings.TELEGRAM_BUILDER_BOT_ADMINS
        or message.from_user.id in await get_whitelist_users()
    )


def whitelisted_only(
    func: Callable[[Update, CustomContext], Awaitable[Any]],
) -> Callable[[Update, CustomContext], Awaitable[Any]]:
    @wraps(func)
    async def wrapper(update: Update, context: CustomContext, *args: Any, **kwargs: Any) -> Any:
        if not await is_whitelisted_user(update.message):
            return None
        return await func(update, context, *args, **kwargs)

    return wrapper
