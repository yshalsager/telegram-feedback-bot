from django.conf import settings
from telegram import Message

from feedback_bot.telegram.builder.crud import get_whitelist_users


async def is_whitelisted_user(message: Message) -> bool:
    return (
        message.from_user.id in await get_whitelist_users()
        or message.from_user.id in settings.TELEGRAM_BUILDER_BOT_ADMINS
    )
