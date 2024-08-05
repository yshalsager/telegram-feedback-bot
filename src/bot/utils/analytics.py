from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast

from pyrogram import Client
from pyrogram.types import Message

from src.bot.db.crud import add_chat_to_db
from src.bot.db.session import session_scope
from src.bot.utils.telegram import get_chat_title, get_chat_type

F = TypeVar('F', bound=Callable[..., Any])


def add_new_chat_to_db(func: F) -> F:
    @wraps(func)
    async def wrapper(client: Client, message: Message, *args: list, **kwargs: dict) -> F:
        chat_title = get_chat_title(message)
        assert chat_title is not None
        with session_scope(client.me.id) as session:
            add_chat_to_db(
                session,
                message.chat.id,
                chat_title,
                get_chat_type(message),
            )
        return cast(F, await func(client, message, *args, **kwargs))

    return cast(F, wrapper)
