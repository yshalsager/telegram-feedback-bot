import logging
from typing import Any, Literal, cast

import orjson
from django.conf import settings
from django.http import HttpRequest
from django.utils.translation import activate
from django.utils.translation import gettext_lazy as _
from ninja import Field, Router, Schema
from ninja.errors import AuthenticationError, ValidationError
from ninja.security import HttpBearer
from telegram import Bot
from telegram.constants import MessageLimit
from telegram.error import InvalidToken

from feedback_bot.telegram.builder.crud import (
    bot_exists,
    create_bot,
    update_user_language,
    user_is_whitelisted,
)
from feedback_bot.telegram.utils.mini_app import parse_init_data, validate_mini_app_init_data

logger = logging.getLogger(__name__)


class TelegramMiniAppAuth(HttpBearer):
    """Custom authentication class for Telegram Mini App validation using Bearer token."""

    async def authenticate(self, request: HttpRequest, token: str) -> dict[str, Any]:
        """Validate the Telegram Mini App init data from the Bearer token.

        The token should contain the Telegram Mini App init data.
        """
        if not token:
            raise AuthenticationError('Missing token in Authorization header')

        # The token contains the init data for Telegram Mini App
        init_data = token
        admins = list(settings.TELEGRAM_BUILDER_BOT_ADMINS)
        parsed_data = parse_init_data(init_data)

        if (
            settings.DEBUG
            and (user_data := orjson.loads(parsed_data.get('user', '{}')))
            and (user_data.get('id') in admins or user_data.get('id') == 1)
        ):
            return cast(dict[str, Any], user_data)

        is_valid, user_data = validate_mini_app_init_data(
            parsed_data, settings.TELEGRAM_BUILDER_BOT_TOKEN
        )

        if not is_valid:
            raise AuthenticationError('Invalid Telegram Mini App data')

        if not (user := await user_is_whitelisted(user_data.get('id', 1))):
            raise AuthenticationError('User is not whitelisted')

        user_data['language_code'] = user.language_code

        logger.info(f'Successfully authenticated user: {user_data.get("username")}')
        return user_data


miniapp_auth = TelegramMiniAppAuth()

router = Router()


@router.post(
    '/validate_user/',
    auth=miniapp_auth,
    response={
        200: dict[str, Any],
        401: dict[str, str],
    },
    url_name='validate_user',
)
async def validate_user(request: HttpRequest) -> dict[str, Any]:
    """Validate user endpoint

    The request.auth parameter is automatically populated by the authentication class
    with the validated user data from the Telegram Mini App.
    """
    return {'status': 'success', 'message': 'User successfully validated', 'user': request.auth}


class LanguageIn(Schema):
    language: Literal[*settings.TELEGRAM_LANGUAGES] = Field(..., description='The language to set')


@router.post(
    '/set_language/',
    auth=miniapp_auth,
    response={
        200: dict[str, Any],
        401: dict[str, str],
    },
    url_name='set_language',
)
async def set_language(request: HttpRequest, payload: LanguageIn) -> dict[str, Any]:
    """Set language endpoint"""
    user_data = request.auth
    user_data['language_code'] = payload.language
    await update_user_language(user_data['id'], payload.language)
    return {'status': 'success', 'message': 'Language set successfully', 'user': user_data}


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


async def validate_bot_token(bot_token: str) -> bool:
    """
    Validate a Telegram bot token using python-telegram-bot.

    Args:
        bot_token: The bot token to validate

    Returns:
        dict: Bot information if valid

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
    '/add_bot/',
    auth=miniapp_auth,
    response={200: dict[str, Any], 400: dict[str, str]},
    url_name='add_bot',
)
async def add_bot(request: HttpRequest, payload: AddBotIn) -> dict[str, Any]:
    """Add bot endpoint"""
    user_data = request.auth
    activate(user_data['language_code'])
    try:
        bot_info = await validate_bot_token(payload.bot_token)
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

    if not settings.TELEGRAM_NEW_BOT_ADMIN_APPROVAL:
        try:
            ptb_bot = Bot(token=bot.token)
            await ptb_bot.set_webhook(
                f'{settings.TELEGRAM_BUILDER_BOT_WEBHOOK_URL}/api/webhook/{bot.uuid}'
            )
        except Exception as err:  # noqa: BLE001
            return 400, {'status': 'error', 'message': f'Failed to set webhook: {err}'}

    return 200, {'status': 'success', 'bot': bot_info}
