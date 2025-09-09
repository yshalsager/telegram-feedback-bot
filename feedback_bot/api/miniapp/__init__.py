import logging
from importlib import import_module
from pathlib import Path
from typing import Any, cast

import orjson
from django.conf import settings
from django.http import HttpRequest
from ninja import Router
from ninja.errors import AuthenticationError
from ninja.security import HttpBearer

from feedback_bot.crud import user_is_whitelisted
from feedback_bot.telegram.utils.mini_app import parse_init_data, validate_mini_app_init_data
from feedback_bot.utils.modules_loader import get_modules

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

router = Router(auth=miniapp_auth)

for module in get_modules(Path(__file__).parent):
    import_module(module.name)
