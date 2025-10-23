from typing import Any
from uuid import UUID

from django.conf import settings
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from ninja import Field, Schema
from ninja.errors import ValidationError
from telegram import Bot, Update
from telegram.constants import MessageLimit
from telegram.error import InvalidToken

from feedback_bot.api.miniapp import router
from feedback_bot.api.miniapp.decorators import with_locale
from feedback_bot.crud import (
    bot_exists,
    create_bot,
    delete_bot,
    ensure_user_ban,
    get_bot,
    get_bot_stats,
    get_bot_token,
    get_bots,
    lift_user_ban,
    list_banned_users,
    update_bot_settings,
)
from feedback_bot.models import BannedUser, BotStats
from feedback_bot.models import Bot as BotModel
from feedback_bot.telegram.utils.cryptography import generate_bot_webhook_secret


class AddBotIn(Schema):
    bot_token: str = Field(
        ..., description='The token of the bot to add', pattern=r'^[0-9]{8,10}:[a-zA-Z0-9_-]{35}$'
    )
    enable_confirmations: bool = Field(default=True, description='Whether to enable confirmations')
    start_message: str = Field(
        ..., description='The start message for the bot', max_length=MessageLimit.MAX_TEXT_LENGTH
    )
    feedback_received_message: str = Field(
        ...,
        description='The feedback received message for the bot',
        max_length=MessageLimit.MAX_TEXT_LENGTH,
    )


class UpdateBotIn(Schema):
    enable_confirmations: bool | None = Field(alias='confirmations_on', default=None)
    start_message: str | None = Field(
        default=None,
        description='Updated start message',
        max_length=MessageLimit.MAX_TEXT_LENGTH,
    )
    feedback_received_message: str | None = Field(
        default=None,
        description='Updated feedback received message',
        max_length=MessageLimit.MAX_TEXT_LENGTH,
    )
    enabled: bool | None = Field(default=None)


class StatusMessage(Schema):
    status: str
    message: str


class BotInfoOut(Schema):
    telegram_id: int
    username: str
    name: str


class AddBotOut(Schema):
    status: str
    bot: BotInfoOut


class BanUserIn(Schema):
    user_telegram_id: int = Field(..., ge=1, description='Telegram user ID to ban')
    reason: str | None = Field(
        default=None, description='Optional reason for banning', max_length=512
    )


class BanMutationResponse(Schema):
    status: str
    message: str
    user_telegram_id: int
    created: bool
    reason: str | None = Field(default=None)


class UnbanMutationResponse(Schema):
    status: str
    message: str
    user_telegram_id: int
    removed: bool


class BotStatsOut(Schema):
    incoming_messages: int
    outgoing_messages: int

    class Meta:
        from_attributes = True


class BannedUserOut(Schema):
    user_telegram_id: int
    created_at: str = Field(..., alias='created_at.isoformat')
    reason: str | None = Field(default=None)

    class Meta:
        from_attributes = True


class BotOut(Schema):
    uuid: UUID
    name: str
    telegram_id: int
    username: str
    owner_username: str = Field(..., alias='owner.username')
    owner_telegram_id: int = Field(..., alias='owner.telegram_id')
    start_message: str
    feedback_received_message: str
    confirmations_on: bool
    enabled: bool
    forward_chat_id: int | None
    created_at: str = Field(..., alias='created_at.isoformat')
    updated_at: str = Field(..., alias='updated_at.isoformat')

    class Meta:
        from_attributes = True


async def validate_bot_token(bot_token: str) -> dict[str, Any]:
    """
    Validate a Telegram bot token using python-telegram-bot.

    Args:
        bot_token: The bot token to validate

    Returns:
        dict[str, Any]: Bot information if valid

    Raises:
        ValidationError: If the bot token is invalid
    """
    try:
        bot = Bot(token=bot_token)
        await bot.get_me()
        return {
            'name': bot.first_name + (f' {bot.last_name}' if bot.last_name else ''),
            'telegram_id': bot.id,
            'username': bot.username,
        }
    except InvalidToken as err:
        raise ValidationError(str(_('invalid_bot_token'))) from err
    except Exception as err:
        raise ValidationError(str(_('unable_to_validate_bot_token'))) from err


@router.post(
    '/bot/',
    response={200: AddBotOut, 400: StatusMessage},
    url_name='add_bot',
)
@with_locale
async def add_bot(  # noqa: PLR0911
    request: HttpRequest, payload: AddBotIn
) -> tuple[int, dict[str, Any]]:
    """Add bot endpoint"""
    user_data = request.auth
    try:
        bot_info = await validate_bot_token(payload.bot_token)
    except ValidationError as err:
        return 400, {'status': 'error', 'message': str(err)}
    except Exception as err:  # noqa: BLE001
        return 400, {'status': 'error', 'message': str(err)}

    if payload.bot_token == settings.TELEGRAM_BUILDER_BOT_TOKEN:
        return 400, {'status': 'error', 'message': str(_('cannot_add_builder_bot'))}

    bot_already_exists = await bot_exists(bot_info['telegram_id'])
    if bot_already_exists:
        return 400, {'status': 'error', 'message': str(_('bot_already_exists'))}

    bot = await create_bot(
        bot_info['telegram_id'],
        payload.bot_token,
        bot_info['username'],
        bot_info['name'],
        user_data['id'],
        payload.enable_confirmations,
        payload.start_message,
        payload.feedback_received_message,
    )

    if not bot:
        return 400, {'status': 'error', 'message': 'Failed to add bot'}

    if settings.TELEGRAM_NEW_BOT_ADMIN_APPROVAL:
        return 200, {'status': 'success', 'bot': bot_info}

    try:
        ptb_bot = Bot(token=bot.token)
        await ptb_bot.set_webhook(
            f'{settings.TELEGRAM_BUILDER_BOT_WEBHOOK_URL}/api/webhook/{bot.uuid}/',
            secret_token=generate_bot_webhook_secret(bot.uuid),
            allowed_updates=Update.ALL_TYPES,
        )
    except Exception as err:  # noqa: BLE001
        return 400, {'status': 'error', 'message': f'Failed to set webhook: {err}'}

    return 200, {'status': 'success', 'bot': bot_info}


@router.get(
    '/bot/',
    response=list[BotOut],
    url_name='list_bots',
)
async def list_bots(request: HttpRequest) -> list[BotModel]:
    return await get_bots(request.auth['id'])


@router.get(
    '/bot/{bot_uuid}/',
    response={200: BotOut, 404: StatusMessage},
    url_name='get_bot',
)
@with_locale
async def retrieve_bot(
    request: HttpRequest, bot_uuid: UUID
) -> tuple[int, BotModel | dict[str, str]]:
    user_data = request.auth

    bot = await get_bot(bot_uuid, user_data['id'])
    if not bot:
        return 404, {'status': 'error', 'message': str(_('bot_not_found'))}

    return 200, bot


@router.put(
    '/bot/{bot_uuid}/',
    response={200: BotOut, 400: StatusMessage, 404: StatusMessage},
    url_name='update_bot',
)
@with_locale
async def update_bot(
    request: HttpRequest, bot_uuid: UUID, payload: UpdateBotIn
) -> tuple[int, BotModel | dict[str, str]]:
    user_data = request.auth
    update_data = payload.dict(exclude_unset=True)

    if 'enable_confirmations' in update_data:
        update_data['confirmations_on'] = update_data.pop('enable_confirmations')

    if not update_data:
        return 400, {'status': 'error', 'message': str(_('no_fields_to_update'))}

    existing_bot = await get_bot(bot_uuid, user_data['id'])
    if not existing_bot:
        return 404, {'status': 'error', 'message': str(_('bot_not_found'))}

    bot = await update_bot_settings(bot_uuid, user_data['id'], update_data)
    if not bot:
        return 404, {'status': 'error', 'message': str(_('bot_not_found'))}

    if 'enabled' in update_data and update_data['enabled'] != existing_bot.enabled:
        bot_token = await get_bot_token(bot_uuid, user_data['id'])
        if not bot_token:
            return 404, {'status': 'error', 'message': str(_('bot_not_found'))}
        ptb_bot = Bot(token=bot_token)
        webhook_url = f'{settings.TELEGRAM_BUILDER_BOT_WEBHOOK_URL}/api/webhook/{bot.uuid}/'
        try:
            if bot.enabled:
                await ptb_bot.set_webhook(
                    webhook_url,
                    secret_token=generate_bot_webhook_secret(str(bot.uuid)),
                    allowed_updates=Update.ALL_TYPES,
                )
            else:
                await ptb_bot.delete_webhook()
        except Exception as err:  # noqa: BLE001
            await update_bot_settings(bot_uuid, user_data['id'], {'enabled': existing_bot.enabled})
            return 400, {'status': 'error', 'message': f'Failed to update webhook: {err}'}

    return 200, bot


@router.delete(
    '/bot/{bot_uuid}/forward_chat/',
    response={200: StatusMessage, 404: StatusMessage},
    url_name='unlink_bot_forward_chat',
)
@with_locale
async def unlink_bot_forward_chat(
    request: HttpRequest, bot_uuid: UUID
) -> tuple[int, dict[str, str]]:
    user_data = request.auth

    bot = await update_bot_settings(bot_uuid, user_data['id'], {'forward_chat_id': None})
    if not bot:
        return 404, {'status': 'error', 'message': str(_('bot_not_found'))}

    return 200, {'status': 'success', 'message': 'Bot unlinked from group.'}


@router.delete(
    '/bot/{bot_uuid}/',
    response={200: StatusMessage, 404: StatusMessage},
    url_name='delete_bot',
)
@with_locale
async def remove_bot(request: HttpRequest, bot_uuid: UUID) -> tuple[int, dict[str, str]]:
    user_data = request.auth

    deleted = await delete_bot(bot_uuid, user_data['id'])
    if not deleted:
        return 404, {'status': 'error', 'message': str(_('bot_not_found'))}

    return 200, {'status': 'success', 'message': str(_('bot_deleted'))}


@router.get(
    '/bot/{bot_uuid}/stats/',
    response={200: BotStatsOut, 404: StatusMessage},
    url_name='bot_stats',
)
@with_locale
async def retrieve_bot_stats(
    request: HttpRequest, bot_uuid: UUID
) -> tuple[int, BotStats | dict[str, str]]:
    user_data = request.auth

    stats = await get_bot_stats(bot_uuid, user_data['id'])
    if not stats:
        return 404, {'status': 'error', 'message': str(_('bot_not_found'))}

    return 200, stats


@router.get(
    '/bot/{bot_uuid}/banned_users/',
    response={200: list[BannedUserOut], 404: StatusMessage},
    url_name='list_banned_users',
)
@with_locale
async def retrieve_banned_users(
    request: HttpRequest, bot_uuid: UUID
) -> tuple[int, list[BannedUser] | dict[str, str]]:
    user_id = request.auth['id']

    bot = await get_bot(bot_uuid, user_id)
    if not bot:
        return 404, {'status': 'error', 'message': str(_('bot_not_found'))}

    return 200, await list_banned_users(bot.id)


@router.post(
    '/bot/{bot_uuid}/banned_users/',
    response={200: BanMutationResponse, 404: StatusMessage},
    url_name='ban_user',
)
@with_locale
async def ban_user(
    request: HttpRequest, bot_uuid: UUID, payload: BanUserIn
) -> BanMutationResponse | tuple[int, dict[str, str]]:
    user_id = request.auth['id']

    bot = await get_bot(bot_uuid, user_id)
    if not bot:
        return 404, {'status': 'error', 'message': str(_('bot_not_found'))}

    reason = payload.reason.strip() if isinstance(payload.reason, str) else ''

    banned_user, created = await ensure_user_ban(
        bot.id,
        payload.user_telegram_id,
        reason=reason,
    )
    message = (
        str(_('User %(user_id)d banned.'))
        if created
        else str(_('User %(user_id)d was already banned.'))
    ) % {'user_id': banned_user.user_telegram_id}

    return 200, {
        'status': 'success',
        'message': message,
        'user_telegram_id': banned_user.user_telegram_id,
        'created': created,
        'reason': banned_user.reason,
    }


@router.delete(
    '/bot/{bot_uuid}/banned_users/{user_telegram_id}/',
    response={200: UnbanMutationResponse, 404: StatusMessage},
    url_name='unban_user',
)
@with_locale
async def unban_user(
    request: HttpRequest, bot_uuid: UUID, user_telegram_id: int
) -> tuple[int, dict[str, Any]]:
    user_id = request.auth['id']

    bot = await get_bot(bot_uuid, user_id)
    if not bot:
        return 404, {'status': 'error', 'message': str(_('bot_not_found'))}

    removed = await lift_user_ban(bot.id, user_telegram_id)
    message = (
        str(_('User %(user_id)d unbanned.'))
        if removed
        else str(_('User %(user_id)d was not banned.'))
    ) % {'user_id': user_telegram_id}

    return 200, {
        'status': 'success',
        'message': message,
        'user_telegram_id': user_telegram_id,
        'removed': removed,
    }
