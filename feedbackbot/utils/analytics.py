from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast

from pyrogram import Client
from pyrogram.types import Message

from feedbackbot.db.curd import add_chat_to_db
from feedbackbot.utils.telegram import get_chat_title, get_chat_type

F = TypeVar("F", bound=Callable[..., Any])


def add_new_chat_to_db(func: F) -> F:
    @wraps(func)
    async def wrapper(client: Client, message: Message, *args: list, **kwargs: dict) -> F:
        chat_title = get_chat_title(message)
        assert chat_title is not None
        add_chat_to_db(
            message.chat.id,
            chat_title,
            get_chat_type(message),
        )
        return cast(F, await func(client, message, *args, **kwargs))

    return cast(F, wrapper)
