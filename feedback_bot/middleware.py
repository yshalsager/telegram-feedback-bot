from collections.abc import Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden


class TelegramSecretTokenMiddleware:
    def __init__(self, get_response: Callable) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if not request.path.startswith(f'/{settings.TELEGRAM_BUILDER_BOT_WEBHOOK_NAME}'):
            return self.get_response(request)

        secret_token = request.headers.get('X-Telegram-Bot-Api-Secret-Token')
        if not secret_token or secret_token != settings.TELEGRAM_BUILDER_BOT_WEBHOOK_SECRET:
            return HttpResponseForbidden('Invalid secret token.')

        return self.get_response(request)
