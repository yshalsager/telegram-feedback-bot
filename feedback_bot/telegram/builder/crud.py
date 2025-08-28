from typing import Any

from django.conf import settings

from feedback_bot.models import User


async def create_user(user_data: dict[str, Any]) -> tuple[User, bool]:
    user, created = await User.objects.aget_or_create(
        telegram_id=user_data.get('id'),
        defaults={
            'telegram_id': user_data.get('id'),
            'username': user_data.get('username'),
            'language_code': user_data.get('language_code'),
            'is_whitelisted': True,
            'is_admin': user_data.get('id') in settings.TELEGRAM_BUILDER_BOT_ADMINS,
        },
    )
    return user, created
