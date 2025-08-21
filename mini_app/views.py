import logging

import orjson
from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from mini_app.utils import validate_mini_app_init_data

logger = logging.getLogger(__name__)


@csrf_exempt
def app(request: HttpRequest) -> HttpResponse:
    return render(request, 'index.html')


@csrf_exempt
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
