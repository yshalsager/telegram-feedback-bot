from typing import Any

from django.conf import settings

from feedback_bot.models import Bot, User
from feedback_bot.telegram.utils.cryptography import decrypt_token


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


async def get_user(user_id: int, **kwargs: Any) -> User | None:
    return await User.objects.filter(telegram_id=user_id, **kwargs).afirst()


async def get_user_language(user_id: int) -> str:
    return (
        await User.objects.filter(telegram_id=user_id)
        .values_list('language_code', flat=True)
        .afirst()
        or 'en'
    )


async def user_is_whitelisted(user_id: int) -> User | None:
    return await get_user(user_id, is_whitelisted=True)


async def get_whitelist_users() -> list[int]:
    return [
        telegram_id
        async for telegram_id in User.objects.filter(is_whitelisted=True).values_list(
            'telegram_id', flat=True
        )
    ]


async def update_user_language(user_id: int, language_code: str) -> None:
    await User.objects.filter(telegram_id=user_id).aupdate(language_code=language_code)


async def create_bot(
    telegram_id: int,
    bot_token: str,
    username: str,
    name: str,
    owner: int,
    enable_confirmations: bool,
    start_message: str,
    feedback_received_message: str,
) -> Bot:
    bot = await Bot.objects.acreate(
        telegram_id=telegram_id,
        username=username,
        name=name,
        token=bot_token,
        owner_id=owner,
        enabled=not settings.TELEGRAM_NEW_BOT_ADMIN_APPROVAL,
        confirmations_on=enable_confirmations,
        start_message=start_message,
        feedback_received_message=feedback_received_message,
    )
    return bot


async def bot_exists(telegram_id: int) -> bool:
    return bool(await Bot.objects.filter(telegram_id=telegram_id).afirst())


async def get_bots_keys():
    """Get all enabled bots with their UUID and token."""
    return [
        (bot[0], decrypt_token(bot[1]))
        async for bot in Bot.objects.filter(enabled=True).values_list('uuid', '_token')
    ]


async def get_bots_tokens() -> list[str]:
    return [
        decrypt_token(bot_token)
        async for bot_token in Bot.objects.filter(enabled=True).values_list('_token', flat=True)
    ]
