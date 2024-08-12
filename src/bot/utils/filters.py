"""
Bot custom filters
"""

from collections.abc import Callable
from typing import Any

from pyrogram import Client, filters
from pyrogram.types import Message

from src.builder.db.crud import get_bot_owner


def check_if_admin(_: Callable[..., Any], client: Client, message: Message) -> bool:
    """Check if user is admin."""
    return bool(message.from_user and message.from_user.id in {get_bot_owner(client.me.id)})


is_admin = filters.create(check_if_admin)
