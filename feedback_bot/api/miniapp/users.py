from typing import Any, Literal

from django.conf import settings
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from ninja import Field, ModelSchema, Schema
from ninja.errors import HttpError

from feedback_bot.api.miniapp import router
from feedback_bot.api.miniapp.decorators import DEFAULT_LANGUAGE_CODE, with_locale
from feedback_bot.crud import (
    delete_user,
    get_user,
    get_users,
    is_admin_user,
    update_user_details,
    upsert_user,
)
from feedback_bot.models import User as UserModel

LanguageLiteral = Literal[*settings.TELEGRAM_LANGUAGES] if settings.TELEGRAM_LANGUAGES else str


async def _ensure_admin(user_data: dict[str, Any]) -> None:
    try:
        user_id = int(user_data.get('id'))
    except (TypeError, ValueError):
        raise HttpError(403, {'status': 'error', 'message': str(_('not_authorized'))}) from None

    if user_id in settings.TELEGRAM_BUILDER_BOT_ADMINS:
        return

    if await is_admin_user(user_id):
        return

    raise HttpError(403, {'status': 'error', 'message': str(_('not_authorized'))})


def _normalize_username(raw_username: str | None) -> str:
    username = (raw_username or '').strip()
    if username.startswith('@'):
        username = username[1:]

    if len(username) > 32:
        raise HttpError(400, {'status': 'error', 'message': str(_('username_too_long'))})

    if username and not username.replace('_', '').isalnum():
        raise HttpError(400, {'status': 'error', 'message': str(_('username_invalid_characters'))})

    return username


def _user_field_value(user: UserModel, field: str) -> Any:
    value = getattr(user, field)
    if field == 'username':
        return (value or '').strip()
    return value


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


class AddUserIn(Schema):
    telegram_id: int = Field(..., description='Telegram user ID', ge=1)
    username: str | None = Field(
        default=None,
        description='Telegram username (without @)',
        max_length=32,
    )
    language_code: LanguageLiteral = Field(
        default=DEFAULT_LANGUAGE_CODE,
        description='Preferred language code',
    )
    is_whitelisted: bool = Field(
        default=True,
        description='Allow the user to access the mini app',
    )
    is_admin: bool = Field(default=False, description='Grant admin privileges to the user')


class ManageUserIn(Schema):
    username: str | None = Field(
        default=None,
        description='Updated Telegram username (without @)',
        max_length=32,
    )
    language_code: LanguageLiteral | None = Field(
        default=None,
        description='Updated preferred language code',
    )
    is_whitelisted: bool | None = Field(default=None, description='Toggle whitelist access')
    is_admin: bool | None = Field(default=None, description='Toggle admin privileges')


class MutationMessage(Schema):
    status: str
    message: str


class UserMutationResponse(MutationMessage):
    user: UserOut


class ErrorResponse(Schema):
    status: str
    message: str


@router.get(
    '/user/',
    response=list[UserOut],
    url_name='list_users',
)
async def list_users(request: HttpRequest) -> list[UserModel]:
    await _ensure_admin(request.auth)
    return await get_users()


@router.get(
    '/user/{telegram_id}/',
    response={200: UserOut, 403: ErrorResponse, 404: ErrorResponse},
    url_name='get_user',
)
@with_locale
async def retrieve_user(
    request: HttpRequest, telegram_id: int
) -> UserModel | tuple[int, dict[str, Any]]:
    await _ensure_admin(request.auth)

    user = await get_user(telegram_id)
    if not user:
        return 404, {'status': 'error', 'message': str(_('user_not_found'))}

    return user


@router.post(
    '/user/',
    response={
        200: UserMutationResponse,
        400: ErrorResponse,
        403: ErrorResponse,
    },
    url_name='add_user',
)
@with_locale
async def add_user(request: HttpRequest, payload: AddUserIn) -> UserMutationResponse:
    await _ensure_admin(request.auth)

    username = _normalize_username(payload.username)

    try:
        user, created = await upsert_user(
            {
                'id': payload.telegram_id,
                'username': username,
                'language_code': payload.language_code,
                'is_whitelisted': payload.is_whitelisted,
                'is_admin': payload.is_admin,
            }
        )
    except ValueError as err:
        raise HttpError(400, {'status': 'error', 'message': str(err)}) from err

    message = str(_('user_added_successfully')) if created else str(_('user_updated_successfully'))
    user_schema = UserOut.from_orm(user)

    return UserMutationResponse(status='success', message=message, user=user_schema)


@router.put(
    '/user/{telegram_id}/',
    response={
        200: UserMutationResponse,
        400: ErrorResponse,
        403: ErrorResponse,
        404: ErrorResponse,
    },
    url_name='manage_user',
)
@with_locale
async def manage_user(
    request: HttpRequest, telegram_id: int, payload: ManageUserIn
) -> tuple[int, dict[str, Any]]:
    await _ensure_admin(request.auth)

    existing_user = await get_user(telegram_id)
    if not existing_user:
        return 404, {'status': 'error', 'message': str(_('user_not_found'))}

    update_payload = payload.dict(exclude_none=True)

    if 'username' in update_payload:
        update_payload['username'] = _normalize_username(update_payload['username'])

    changes = {
        field: value
        for field, value in update_payload.items()
        if value != _user_field_value(existing_user, field)
    }

    if not changes:
        return 400, {'status': 'error', 'message': str(_('user_no_changes'))}

    updated_user = await update_user_details(telegram_id, changes)
    if not updated_user:
        return 404, {'status': 'error', 'message': str(_('user_not_found'))}

    return 200, {
        'status': 'success',
        'message': str(_('user_updated_successfully')),
        'user': updated_user,
    }


@router.delete(
    '/user/{telegram_id}/',
    response={
        200: MutationMessage,
        403: ErrorResponse,
        404: ErrorResponse,
    },
    url_name='delete_user',
)
@with_locale
async def delete_user_entry(
    request: HttpRequest, telegram_id: int
) -> tuple[int, dict[str, Any]] | MutationMessage:
    await _ensure_admin(request.auth)

    if telegram_id in settings.TELEGRAM_BUILDER_BOT_ADMINS:
        return 403, {'status': 'error', 'message': str(_('cannot_delete_builder_admin'))}

    deleted = await delete_user(telegram_id)
    if not deleted:
        return 404, {'status': 'error', 'message': str(_('user_not_found'))}

    return MutationMessage(status='success', message=str(_('user_deleted_successfully')))
