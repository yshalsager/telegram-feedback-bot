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


async def user_is_whitelisted(user_id: int) -> User | None:
    return await User.objects.filter(telegram_id=user_id, is_whitelisted=True).afirst()


async def get_whitelist_users() -> list[int]:
    return [
        telegram_id
        async for telegram_id in User.objects.filter(is_whitelisted=True).values_list(
            'telegram_id', flat=True
        )
    ]


async def update_user_language(user_id: int, language_code: str) -> None:
    await User.objects.filter(telegram_id=user_id).aupdate(language_code=language_code)
