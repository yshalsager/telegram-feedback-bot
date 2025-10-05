from typing import Any, cast

import orjson
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.http import HttpRequest, HttpResponse
from django.urls import include, path
from ninja import NinjaAPI
from ninja.errors import HttpError
from ninja.renderers import BaseRenderer


class ORJSONRenderer(BaseRenderer):
    media_type = 'application/json'

    def render(self, request: HttpRequest, data: Any, *, response_status: int) -> bytes:
        return cast(bytes, orjson.dumps(data))


api = NinjaAPI(renderer=ORJSONRenderer())


@api.exception_handler(HttpError)
@api.exception_handler(Exception)
def exception_response(request: HttpRequest, exception: Exception) -> HttpResponse:
    if settings.DEBUG:
        raise exception
    if isinstance(exception, ObjectDoesNotExist):
        status_code = 404
    else:
        status_code = getattr(exception, 'status_code', 500)
    if isinstance(exception, IntegrityError):
        message = 'Integrity Error'
    else:
        message = getattr(exception, 'message', repr(exception))
    return api.create_response(
        request,
        data={'error': True, 'message': message, 'success': False},
        status=status_code,
    )


api.add_router('', 'config.api.router')
api.add_router('', 'feedback_bot.api.miniapp.router')
api.add_router('webhook', 'feedback_bot.api.webhooks.router')

urlpatterns = [
    path('api/', api.urls),
    path('', include('feedback_bot.urls')),
]
