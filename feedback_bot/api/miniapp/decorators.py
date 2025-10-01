"""Reusable decorators for miniapp API views."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, ParamSpec, TypeVar

from django.conf import settings
from django.http import HttpRequest
from django.utils.translation import activate

P = ParamSpec('P')
R = TypeVar('R')

DEFAULT_LANGUAGE_CODE = settings.TELEGRAM_LANGUAGES[0] if settings.TELEGRAM_LANGUAGES else 'en'


def _get_request(args: tuple[Any, ...], kwargs: dict[str, Any]) -> HttpRequest | None:
    candidate = args[0] if args else kwargs.get('request')

    return candidate if isinstance(candidate, HttpRequest) else None


def with_locale[**P, R](func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
    """Activate the requester's locale before executing the view."""

    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        request = _get_request(args, kwargs)
        if request is None:
            raise TypeError('with_locale requires the first argument to be HttpRequest.')

        auth = getattr(request, 'auth', None)
        language_code = None
        if isinstance(auth, dict):
            language_code = auth.get('language_code')

        activate(language_code or DEFAULT_LANGUAGE_CODE)
        return await func(*args, **kwargs)

    return wrapper


__all__ = ['DEFAULT_LANGUAGE_CODE', 'with_locale']
