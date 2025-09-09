from typing import Any

from django.http import HttpRequest
from ninja import ModelSchema

from feedback_bot.api.miniapp import router
from feedback_bot.crud import get_users
from feedback_bot.models import User as UserModel


@router.post(
    '/validate_user/',
    response={
        200: dict[str, Any],
        401: dict[str, str],
    },
    url_name='validate_user',
)
async def validate_user(request: HttpRequest) -> dict[str, Any]:
    """Validate user endpoint

    The request.auth parameter is automatically populated by the authentication class
    with the validated user data from the Telegram Mini App.
    """
    return {'status': 'success', 'message': 'User successfully validated', 'user': request.auth}


class UserOut(ModelSchema):
    class Meta:
        model = UserModel
        fields = '__all__'


@router.get(
    '/user/',
    response=list[UserOut],
    url_name='get_user',
)
async def get_user(request: HttpRequest) -> list[UserModel]:
    return await get_users()
