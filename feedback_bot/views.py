import logging

import orjson
from django.conf import settings
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt, get_token
from django.views.decorators.http import require_http_methods
from telegram import Update
from telegram.ext import Application

from feedback_bot.models import Bot
from feedback_bot.telegram.bot import WebhookUpdate
from feedback_bot.utils.telegram import validate_mini_app_init_data

logger = logging.getLogger(__name__)


def get_csrf_token(request: HttpRequest) -> JsonResponse:
    return JsonResponse({'csrf_token': get_token(request)})


# @csrf_exempt
def validate_user(request: HttpRequest) -> JsonResponse:
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

    try:
        body = orjson.loads(request.body)
        init_data = body.get('initData')

        if not init_data:
            return JsonResponse({'status': 'error', 'message': 'initData not provided'}, status=400)

        is_valid, user_data = validate_mini_app_init_data(
            init_data, settings.TELEGRAM_BUILDER_BOT_TOKEN
        )

        if not is_valid:
            return JsonResponse({'status': 'error', 'message': 'Invalid data'}, status=403)

        logger.info(f'Successfully validated user: {user_data.get("username")}')
        return JsonResponse({'status': 'success', 'user': user_data})

    except orjson.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.exception('An unexpected error occurred during validation.')
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


# This is the handler for your MAIN BUILDER BOT
@csrf_exempt
async def telegram_webhook_handler(request: HttpRequest) -> HttpResponse:
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


# This is the handler for your INDIVIDUAL FEEDBACK BOTS
@csrf_exempt
async def feedback_bot_webhook_handler(request: HttpRequest, bot_uuid: str) -> HttpResponse:
    try:
        bot_config = await Bot.objects.aget(uuid=bot_uuid, enabled=True)
    except Bot.DoesNotExist:
        return HttpResponseBadRequest('Bot not found or disabled')

    # TODO: Implement the logic from your handlers.py here
    # You will need to build a temporary PTB application for this bot
    # and process the update directly, since the main `ptb_application`
    # is only for the builder bot.
    logger.info(f'Received update for feedback bot @{bot_config.username}')

    return HttpResponse('OK')


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


# @method_decorator(csrf_exempt, name='dispatch')
# class TelegramWebhookView(View):
#     """Handle incoming Telegram webhook updates using UUID for security"""

#     async def post(self, request: HttpRequest, bot_uuid: str) -> HttpRequest:
#         try:
#             try:
#                 bot_config = Bot.objects.get(uuid=bot_uuid, enabled=True)
#             except Bot.DoesNotExist:
#                 return HttpResponseBadRequest('Bot not found or disabled')

#             # Parse update
#             update_data = orjson.loads(request.body)
#             update = Update.de_json(update_data, bot=None)

#             # Process update
#             # await process_update(update, bot_config)

#             return HttpResponse('OK')

#         except orjson.JSONDecodeError:
#             return HttpResponseBadRequest('Invalid JSON')
#         except Exception as e:
#             logger.error(f'Error processing webhook: {e}')
#             return HttpResponseBadRequest('Internal error')


@csrf_exempt
@require_http_methods(['GET'])
def health_check(request: HttpRequest) -> HttpResponse:
    return HttpResponse('Bot is running', content_type='text/plain')
