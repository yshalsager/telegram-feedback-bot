from typing import Any
from uuid import UUID

from django.conf import settings
from django.db.models import Q

from feedback_bot.models import (
    Bot,
    BotStats,
    BroadcastMessage,
    FeedbackChat,
    MessageMapping,
    User,
)
from feedback_bot.telegram.utils.cryptography import decrypt_token

BOT_MANAGEMENT_FIELDS = (
    'name',
    'telegram_id',
    'username',
    'uuid',
    'enabled',
    'confirmations_on',
    'start_message',
    'feedback_received_message',
    'forward_chat_id',
    'owner__username',
    'owner__telegram_id',
    'created_at',
    'updated_at',
)


async def create_user(user_data: dict[str, Any]) -> tuple[User, bool]:
    """Create a user or update the existing entry with the provided data."""

    return await upsert_user(user_data)


async def upsert_user(user_data: dict[str, Any]) -> tuple[User, bool]:
    telegram_id = user_data.get('telegram_id') or user_data.get('id')
    if telegram_id is None:
        raise ValueError('User data must include "id" or "telegram_id"')

    try:
        telegram_id = int(telegram_id)
    except (TypeError, ValueError) as exc:
        raise ValueError('Invalid telegram ID') from exc

    username = user_data.get('username')
    username = '' if username is None else username.strip()

    language_code = user_data.get('language_code') or (
        settings.TELEGRAM_LANGUAGES[0] if settings.TELEGRAM_LANGUAGES else 'en'
    )

    defaults = {
        'username': username,
        'language_code': language_code,
        'is_whitelisted': user_data.get('is_whitelisted', True),
        'is_admin': user_data.get('is_admin', telegram_id in settings.TELEGRAM_BUILDER_BOT_ADMINS),
    }

    user, created = await User.objects.aget_or_create(
        telegram_id=telegram_id,
        defaults={'telegram_id': telegram_id, **defaults},
    )

    if not created:
        await User.objects.filter(telegram_id=telegram_id).aupdate(**defaults)
        user = await User.objects.aget(telegram_id=telegram_id)

    return user, created


async def get_user(user_id: int, **kwargs: Any) -> User | None:
    return await User.objects.filter(telegram_id=user_id, **kwargs).afirst()


async def is_admin_user(user_id: int) -> bool:
    return bool(
        await User.objects.filter(telegram_id=user_id, is_admin=True).only('is_admin').afirst()
    )


async def update_user_details(telegram_id: int, data: dict[str, Any]) -> User | None:
    """Update selected fields on a user and return the updated instance."""

    if not data:
        return await get_user(telegram_id)

    updated = await User.objects.filter(telegram_id=telegram_id).aupdate(**data)
    if not updated:
        return None

    return await User.objects.aget(telegram_id=telegram_id)


async def delete_user(telegram_id: int) -> bool:
    deleted, _ = await User.objects.filter(telegram_id=telegram_id).adelete()
    return bool(deleted)


async def get_users() -> list[User]:
    return [user async for user in User.objects.all()]


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


async def ensure_feedback_chat(
    bot: Bot, user_telegram_id: int, username: str | None
) -> FeedbackChat:
    defaults = {'username': (username or '').strip()}
    chat, created = await FeedbackChat.objects.aget_or_create(
        bot=bot,
        user_telegram_id=user_telegram_id,
        defaults=defaults,
    )
    if not created and defaults['username'] and chat.username != defaults['username']:
        chat.username = defaults['username']
        await chat.asave(update_fields=['username'])
    return chat


async def set_feedback_chat_topic(chat: FeedbackChat, topic_id: int | None) -> FeedbackChat:
    chat.topic_id = topic_id
    await chat.asave(update_fields=['topic_id'])
    return chat


async def clear_feedback_chat_mappings(bot: Bot, chat: FeedbackChat) -> None:
    await MessageMapping.objects.filter(bot=bot, user_chat=chat).adelete()


async def get_user_message_mapping(
    bot: Bot, user_telegram_id: int, user_message_id: int
) -> MessageMapping | None:
    return (
        await MessageMapping.objects.select_related('user_chat')
        .filter(
            bot=bot,
            user_chat__user_telegram_id=user_telegram_id,
            user_message_id=user_message_id,
        )
        .afirst()
    )


async def get_owner_message_mapping(bot: Bot, owner_message_id: int) -> MessageMapping | None:
    return (
        await MessageMapping.objects.select_related('user_chat')
        .filter(bot=bot, owner_message_id=owner_message_id)
        .afirst()
    )


async def save_incoming_mapping(
    bot: Bot, chat: FeedbackChat, user_message_id: int, owner_message_id: int
) -> None:
    await MessageMapping.objects.aupdate_or_create(
        bot=bot,
        user_message_id=user_message_id,
        defaults={'user_chat': chat, 'owner_message_id': owner_message_id},
    )


async def update_incoming_mapping(bot: Bot, user_message_id: int, owner_message_id: int) -> None:
    await MessageMapping.objects.filter(bot=bot, user_message_id=user_message_id).aupdate(
        owner_message_id=owner_message_id
    )


async def save_outgoing_mapping(
    bot: Bot, chat: FeedbackChat, user_message_id: int, owner_message_id: int
) -> None:
    await MessageMapping.objects.aupdate_or_create(
        bot=bot,
        user_message_id=user_message_id,
        defaults={'user_chat': chat, 'owner_message_id': owner_message_id},
    )


async def bump_incoming_messages(bot: Bot) -> None:
    stats, _ = await BotStats.objects.aget_or_create(bot=bot)
    stats.incoming_messages += 1
    await stats.asave(update_fields=['incoming_messages'])


async def bump_outgoing_messages(bot: Bot) -> None:
    stats, _ = await BotStats.objects.aget_or_create(bot=bot)
    stats.outgoing_messages += 1
    await stats.asave(update_fields=['outgoing_messages'])


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


async def get_bot_config(uuid: str) -> Bot:
    return (
        await Bot.objects.filter(uuid=uuid, enabled=True)
        .only(
            'owner',
            'start_message',
            'feedback_received_message',
            'forward_chat_id',
            'confirmations_on',
            '_token',
        )
        .afirst()
    )


async def get_bots(owner: int) -> list[Bot]:
    qs = Bot.objects.select_related('owner').only(*BOT_MANAGEMENT_FIELDS)
    if owner in settings.TELEGRAM_BUILDER_BOT_ADMINS:
        return [bot async for bot in qs.all()]
    return [bot async for bot in qs.filter(owner=owner)]


def _bot_owner_filter(bot_uuid: UUID | str, owner: int) -> Q:
    filters = Q(uuid=bot_uuid)
    if owner not in settings.TELEGRAM_BUILDER_BOT_ADMINS:
        filters &= Q(owner_id=owner)
    return filters


async def get_builder_broadcast_targets() -> list[int]:
    qs = (
        Bot.objects.filter(owner__telegram_id__isnull=False)
        .values_list('owner__telegram_id', flat=True)
        .distinct()
    )
    return [chat_id async for chat_id in qs]


async def get_feedback_chat_targets(bot: Bot | int) -> list[int]:
    if isinstance(bot, Bot):
        qs = bot.feedback_chats.values_list('user_telegram_id', flat=True).distinct()
    else:
        qs = (
            FeedbackChat.objects.filter(bot_id=bot)
            .values_list('user_telegram_id', flat=True)
            .distinct()
        )
    return [chat_id async for chat_id in qs]


async def record_broadcast_message(
    *, bot: Bot | int | None, chat_id: int, message_id: int
) -> BroadcastMessage:
    payload: dict[str, int | Bot] = {
        'chat_id': chat_id,
        'message_id': message_id,
    }
    if isinstance(bot, Bot):
        payload['bot'] = bot
    elif bot is not None:
        payload['bot_id'] = bot
    return await BroadcastMessage.objects.acreate(**payload)


async def update_bot_settings(bot_uuid: UUID | str, owner: int, data: dict[str, Any]) -> Bot | None:
    if not data:
        return None

    updated = await Bot.objects.filter(_bot_owner_filter(bot_uuid, owner)).aupdate(**data)
    if not updated:
        return None

    return await get_bot(bot_uuid, owner)


async def update_bot_forward_chat_by_telegram_id(
    telegram_id: int, forward_chat_id: int | None
) -> bool:
    """Update the forward chat linked to a bot via its Telegram ID."""

    updated = await Bot.objects.filter(telegram_id=telegram_id).aupdate(
        forward_chat_id=forward_chat_id
    )
    return bool(updated)


async def delete_bot(bot_uuid: UUID | str, owner: int) -> bool:
    deleted, _ = await Bot.objects.filter(_bot_owner_filter(bot_uuid, owner)).adelete()
    return bool(deleted)


async def get_bot(bot_uuid: UUID | str, owner: int) -> Bot | None:
    return (
        await Bot.objects.select_related('owner')
        .only(*BOT_MANAGEMENT_FIELDS)
        .filter(_bot_owner_filter(bot_uuid, owner))
        .afirst()
    )
