import json
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any, TypeVar, cast

from plate import Plate
from pyrogram import Client
from pyrogram.types import CallbackQuery, Message

from src.builder.db.crud import get_user

F = TypeVar('F', bound=Callable[..., Any])

locales_dir = Path(__file__).parent.parent.parent / 'i18n/locales'
languages = json.loads((locales_dir.parent / 'languages.json').read_text())
plate: Plate = Plate(root=str(locales_dir), fallback='en_US')


def get_full_language_code(language_code: str) -> Any:
    for lang in plate.locales:
        if lang.startswith(f'{language_code}_'):
            return lang
    return 'en_US'


def get_translator(language_code: str) -> Any:
    return plate.get_translator(get_full_language_code(language_code))


def get_user_language(update: Message) -> Any:
    user = update.from_user if hasattr(update, 'from_user') else None
    language_code = user.language_code if user else 'en'
    user_db = get_user(user.id) if user else None
    if user_db and user_db.language:
        language_code = user_db.language
    return get_translator(language_code)


def localize(function: F) -> F:
    @wraps(function)
    def wrapper(client: Client, update: Message | CallbackQuery, *args: tuple, **kwargs: dict) -> F:
        i18n = get_user_language(update)
        return cast(F, function(client, update, i18n, *args, **kwargs))

    return cast(F, wrapper)
