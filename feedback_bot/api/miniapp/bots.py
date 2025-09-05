from typing import Any

from django.conf import settings
from django.http import HttpRequest
from django.utils.translation import activate
from django.utils.translation import gettext_lazy as _
from ninja import Field, Schema
from ninja.errors import ValidationError
from telegram import Bot, Update
from telegram.constants import MessageLimit
from telegram.error import InvalidToken

from feedback_bot.api.miniapp import router
from feedback_bot.telegram.crud import bot_exists, create_bot
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
                f'{settings.TELEGRAM_BUILDER_BOT_WEBHOOK_URL}/api/webhook/{bot.uuid}/',
                secret_token=generate_bot_webhook_secret(bot.uuid),
                allowed_updates=Update.ALL_TYPES,
            )
        except Exception as err:  # noqa: BLE001
            return 400, {'status': 'error', 'message': f'Failed to set webhook: {err}'}

    return 200, {'status': 'success', 'bot': bot_info}
