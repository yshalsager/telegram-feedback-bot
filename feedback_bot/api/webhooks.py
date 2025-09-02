import logging

import orjson
from django.conf import settings
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from ninja import Router
from ninja.errors import AuthenticationError
from ninja.security.apikey import APIKeyHeader
from telegram import Bot, Update
from telegram.ext import Application

from feedback_bot.models import Bot as BotConfig
from feedback_bot.telegram.bot import WebhookUpdate
from feedback_bot.telegram.feedback_bot.bot import process_update

logger = logging.getLogger(__name__)


class TelegramSecretTokenAuth(APIKeyHeader):
    """Custom authentication class for Telegram webhook secret token validation."""

    param_name = 'X-Telegram-Bot-Api-Secret-Token'

    def authenticate(self, request: HttpRequest, api_key: str) -> bool:
        """Validate the Telegram secret token."""
        if api_key != settings.TELEGRAM_BUILDER_BOT_WEBHOOK_SECRET:
            raise AuthenticationError('Invalid secret token')

        return True


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
        # logger.info(f'ptb_application._initialized: {ptb_application._initialized}')
        # logger.info(f'Update queued {update}. Queue size: {ptb_application.update_queue.qsize()}')
        return HttpResponse('OK')
    except orjson.JSONDecodeError:
        logger.error('Failed to decode JSON from Telegram.')
        return HttpResponseBadRequest('Invalid JSON')


@router.post('/{bot_uuid}/', url_name='feedback_bot_webhook')
@csrf_exempt
async def feedback_bot_webhook_handler(request: HttpRequest, bot_uuid: str) -> HttpResponse:
    """Handle incoming Telegram updates for a feedback bot"""
    try:
        bot_config = await BotConfig.objects.aget(uuid=bot_uuid, enabled=True)
    except BotConfig.DoesNotExist:
        return HttpResponseBadRequest('Bot not found or disabled')

    try:
        telegram_bot = Bot(token=bot_config.token)
        update = Update.de_json(data=orjson.loads(request.body), bot=telegram_bot)
    except orjson.JSONDecodeError:
        logger.error('Failed to decode JSON from Telegram webhook.')
        return HttpResponseBadRequest('Invalid JSON')
    except (ValueError, TypeError) as e:
        logger.error(f'Failed to parse Telegram update: {e}')
        return HttpResponseBadRequest('Invalid update format')

    await process_update(update, telegram_bot, bot_config)

    return HttpResponse('OK')


@router.post('/submitpayload', url_name='submit_payload')
@csrf_exempt
async def custom_updates(request: HttpRequest) -> HttpResponse:
    ptb_application: Application = request.state['ptb_application']
    try:
        user_id = int(request.GET['user_id'])
        payload = request.GET['payload']
    except (KeyError, ValueError):
        return HttpResponseBadRequest('Invalid `user_id` or `payload` parameters.')

    await ptb_application.update_queue.put(WebhookUpdate(user_id=user_id, payload=payload))
    return HttpResponse('OK')
