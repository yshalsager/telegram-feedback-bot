import logging
from typing import Any

import orjson
from django.conf import settings
from django.http import HttpRequest
from ninja import Router

from feedback_bot.utils.telegram import validate_mini_app_init_data

logger = logging.getLogger(__name__)

router = Router()


@router.post(
    '/validate_user/',
    response={
        200: dict[str, Any],
        404: dict[str, str],
        403: dict[str, str],
        400: dict[str, str],
        500: dict[str, str],
    },
    url_name='validate_user',
)
async def validate_user(request: HttpRequest) -> tuple[int, dict[str, Any]]:
    try:
        body = orjson.loads(request.body)
        init_data = body.get('initData')

        if not init_data:
            return 400, {'status': 'error', 'message': 'initData not provided'}

        is_valid, user_data = validate_mini_app_init_data(
            init_data, settings.TELEGRAM_BUILDER_BOT_TOKEN
        )

        if not is_valid:
            return 403, {'status': 'error', 'message': 'Invalid data'}

        logger.info(f'Successfully validated user: {user_data.get("username")}')
        return 200, {'status': 'success', 'user': user_data}

    except orjson.JSONDecodeError:
        return 400, {'status': 'error', 'message': 'Invalid JSON'}
    except Exception as e:
        logger.exception('An unexpected error occurred during validation.')
        return 500, {'status': 'error', 'message': str(e)}
