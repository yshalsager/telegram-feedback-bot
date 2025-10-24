from typing import Any, NamedTuple
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

BOT_TOKEN_PATTERN = r'^[0-9]{8,10}:[a-zA-Z0-9_-]{30,64}$'  # noqa: S105


class TokenUpdate(NamedTuple):
    changed: bool
    new_token: str | None
    previous_token: str | None


class AddBotIn(Schema):
    bot_token: str = Field(
        ..., description='The token of the bot to add', pattern=BOT_TOKEN_PATTERN
    )
    start_message: str = Field(
        ..., description='The start message for the bot', max_length=MessageLimit.MAX_TEXT_LENGTH
    )
    feedback_received_message: str = Field(
        ...,
        description='The feedback received message for the bot',
        max_length=MessageLimit.MAX_TEXT_LENGTH,
    )


class UpdateBotIn(Schema):
    bot_token: str | None = Field(default=None, pattern=BOT_TOKEN_PATTERN)
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
    allow_photo_messages: bool | None = Field(default=None)
    allow_video_messages: bool | None = Field(default=None)
    allow_voice_messages: bool | None = Field(default=None)
    allow_document_messages: bool | None = Field(default=None)
    allow_sticker_messages: bool | None = Field(default=None)


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
    enabled: bool
    forward_chat_id: int | None
    allow_photo_messages: bool
    allow_video_messages: bool
    allow_voice_messages: bool
    allow_document_messages: bool
    allow_sticker_messages: bool
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


def _build_update_payload(payload: UpdateBotIn) -> dict[str, Any]:
    return payload.dict(exclude_unset=True)


async def _prepare_token_update(  # noqa: PLR0911
    bot_uuid: UUID,
    owner_id: int,
    existing_bot: BotModel,
    update_data: dict[str, Any],
) -> tuple[TokenUpdate, tuple[int, dict[str, str]] | None]:
    new_token = update_data.get('bot_token')
    if new_token is None:
        update_data.pop('bot_token', None)
        return TokenUpdate(False, None, None), None

    new_token = new_token.strip()
    if not new_token:
        update_data.pop('bot_token', None)
        return TokenUpdate(False, None, None), None

    if new_token == settings.TELEGRAM_BUILDER_BOT_TOKEN:
        return TokenUpdate(False, None, None), (
            400,
            {'status': 'error', 'message': str(_('cannot_use_builder_bot_token'))},
        )

    previous_token = await get_bot_token(bot_uuid, owner_id)
    if not previous_token:
        return TokenUpdate(False, None, None), (
            404,
            {'status': 'error', 'message': str(_('bot_not_found'))},
        )

    if new_token == previous_token:
        update_data.pop('bot_token', None)
        return TokenUpdate(False, None, None), None

    try:
        bot_info = await validate_bot_token(new_token)
    except ValidationError as err:
        return TokenUpdate(False, None, None), (400, {'status': 'error', 'message': str(err)})
    except Exception as err:  # noqa: BLE001
        return TokenUpdate(False, None, None), (400, {'status': 'error', 'message': str(err)})

    if bot_info['telegram_id'] != existing_bot.telegram_id:
        return TokenUpdate(False, None, None), (
            400,
            {
                'status': 'error',
                'message': str(_('token_does_not_match_bot')),
            },
        )

    update_data['bot_token'] = new_token
    update_data['name'] = bot_info['name']
    update_data['username'] = bot_info['username']

    return TokenUpdate(True, new_token, previous_token), None


def _admin_approval_error(
    existing_bot: BotModel, update_data: dict[str, Any], user_data: dict[str, Any]
) -> tuple[int, dict[str, str]] | None:
    if (
        settings.TELEGRAM_NEW_BOT_ADMIN_APPROVAL
        and update_data.get('enabled')
        and not existing_bot.enabled
        and not user_data.get('is_admin')
    ):
        return 403, {
            'status': 'error',
            'message': str(_('Admin approval required before enabling this bot')),
        }
    return None


async def _sync_webhook_for_token_change(
    bot_uuid: UUID,
    owner_id: int,
    existing_bot: BotModel,
    bot: BotModel,
    token_update: TokenUpdate,
) -> tuple[int, dict[str, str]] | None:
    if not token_update.changed or not bot.enabled or not token_update.new_token:
        return None

    ptb_bot = Bot(token=token_update.new_token)
    webhook_url = f'{settings.TELEGRAM_BUILDER_BOT_WEBHOOK_URL}/api/webhook/{bot.uuid}/'
    try:
        await ptb_bot.set_webhook(
            webhook_url,
            secret_token=generate_bot_webhook_secret(str(bot.uuid)),
            allowed_updates=Update.ALL_TYPES,
        )
    except Exception as err:  # noqa: BLE001
        if token_update.previous_token is not None:
            await update_bot_settings(
                bot_uuid,
                owner_id,
                {
                    'bot_token': token_update.previous_token,
                    'name': existing_bot.name,
                    'username': existing_bot.username,
                },
            )
        return 400, {'status': 'error', 'message': f'Failed to update webhook: {err}'}

    return None


async def _sync_webhook_for_enabled_change(
    bot_uuid: UUID,
    owner_id: int,
    bot: BotModel,
    existing_bot: BotModel,
    update_data: dict[str, Any],
) -> tuple[int, dict[str, str]] | None:
    if 'enabled' not in update_data or update_data['enabled'] == existing_bot.enabled:
        return None

    bot_token = await get_bot_token(bot_uuid, owner_id)
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
        await update_bot_settings(bot_uuid, owner_id, {'enabled': existing_bot.enabled})
        return 400, {'status': 'error', 'message': f'Failed to update webhook: {err}'}

    return None


@router.put(
    '/bot/{bot_uuid}/',
    response={200: BotOut, 400: StatusMessage, 403: StatusMessage, 404: StatusMessage},
    url_name='update_bot',
)
@with_locale
async def update_bot(  # noqa: PLR0911
    request: HttpRequest, bot_uuid: UUID, payload: UpdateBotIn
) -> tuple[int, BotModel | dict[str, str]]:
    user_data = request.auth
    owner_id = user_data['id']
    update_data = _build_update_payload(payload)

    existing_bot = await get_bot(bot_uuid, owner_id)
    if not existing_bot:
        return 404, {'status': 'error', 'message': str(_('bot_not_found'))}

    token_update, token_error = await _prepare_token_update(
        bot_uuid, owner_id, existing_bot, update_data
    )
    if token_error:
        return token_error

    if not update_data:
        return 400, {'status': 'error', 'message': str(_('no_fields_to_update'))}

    approval_error = _admin_approval_error(existing_bot, update_data, user_data)
    if approval_error:
        return approval_error

    bot = await update_bot_settings(bot_uuid, owner_id, update_data)
    if not bot:
        return 404, {'status': 'error', 'message': str(_('bot_not_found'))}

    token_sync_error = await _sync_webhook_for_token_change(
        bot_uuid, owner_id, existing_bot, bot, token_update
    )
    if token_sync_error:
        return token_sync_error

    enabled_sync_error = await _sync_webhook_for_enabled_change(
        bot_uuid, owner_id, bot, existing_bot, update_data
    )
    if enabled_sync_error:
        return enabled_sync_error

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
