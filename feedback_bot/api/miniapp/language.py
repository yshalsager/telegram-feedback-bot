from typing import Any, Literal

from django.conf import settings
from django.http import HttpRequest
from ninja import Field, Schema

from feedback_bot.api.miniapp import router
from feedback_bot.crud import update_user_language


class LanguageIn(Schema):
    language: Literal[*settings.TELEGRAM_LANGUAGES] = Field(..., description='The language to set')


@router.post(
    '/set_language/',
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
