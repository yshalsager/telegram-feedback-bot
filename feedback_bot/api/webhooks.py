import logging

import orjson
from django.conf import settings
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from ninja import Router
from ninja.errors import AuthenticationError
from ninja.security.apikey import APIKeyHeader
from telegram import Update
from telegram.ext import Application

from feedback_bot.models import Bot as BotConfig
from feedback_bot.telegram.crud import get_bot_config
from feedback_bot.telegram.feedback_bot.bot import build_feedback_bot_application
from feedback_bot.telegram.utils.cryptography import verify_bot_webhook_secret

logger = logging.getLogger(__name__)


class TelegramSecretTokenAuth(APIKeyHeader):
    """Custom authentication class for Telegram webhook secret token validation."""

    param_name = 'X-Telegram-Bot-Api-Secret-Token'

    def authenticate(self, request: HttpRequest, api_key: str) -> bool:
        """Validate the Telegram secret token."""
        # For the main builder bot, use the global secret
        if (
            settings.TELEGRAM_BUILDER_BOT_WEBHOOK_SECRET
            and api_key == settings.TELEGRAM_BUILDER_BOT_WEBHOOK_SECRET
        ):
            return True

        # For feedback bots, extract bot_uuid from URL and verify bot-specific secret
        if (
            bot_uuid := (getattr(request, 'path', '').strip('/').split('/')[-1])
        ) and verify_bot_webhook_secret(bot_uuid, api_key):
            return True

        raise AuthenticationError('Invalid secret token')


telegram_auth = TelegramSecretTokenAuth()
router = Router()


@router.post(
    f'/{settings.TELEGRAM_BUILDER_BOT_WEBHOOK_PATH}',
    url_name='telegram_webhook',
    auth=telegram_auth,
)
@csrf_exempt
async def telegram_webhook(request: HttpRequest) -> HttpResponse:
    """Handle incoming Telegram updates by putting them into the `update_queue`"""
    try:
        ptb_application: Application = request.state['ptb_application']
        update = Update.de_json(data=orjson.loads(request.body), bot=ptb_application.bot)
        await ptb_application.update_queue.put(update)
        return HttpResponse('OK')
    except orjson.JSONDecodeError:
        logger.error('Failed to decode JSON from Telegram.')
        return HttpResponseBadRequest('Invalid JSON')


@router.post('/{bot_uuid}/', url_name='feedback_bot_webhook', auth=telegram_auth)
@csrf_exempt
async def feedback_bot_webhook_handler(request: HttpRequest, bot_uuid: str) -> HttpResponse:
    """Handle incoming Telegram updates for a feedback bot"""
    try:
        bot_config = await get_bot_config(bot_uuid)
    except BotConfig.DoesNotExist:
        return HttpResponseBadRequest('Bot not found or disabled')

    ptb_application = build_feedback_bot_application(bot_config)

    try:
        update = Update.de_json(data=orjson.loads(request.body), bot=ptb_application.bot)
    except orjson.JSONDecodeError as e:
        logger.error(f'Failed to decode JSON from Telegram webhook: {e}')
        return HttpResponseBadRequest('Invalid JSON')
    except (ValueError, TypeError) as e:
        logger.error(f'Failed to parse Telegram update: {e}')
        return HttpResponseBadRequest('Invalid update format')

    async with ptb_application:
        await ptb_application.process_update(update)

    return HttpResponse('OK')
