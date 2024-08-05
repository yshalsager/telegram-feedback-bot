from collections.abc import Callable, Sequence
from typing import Any

from pyrogram import Client, filters
from pyrogram.types import Message


def is_admin(admins_list: Sequence[int]) -> filters.Filter:
    def check_if_admin(_: Callable[[Any], bool], __: Client, message: Message) -> bool:
        """Check if user is admin."""
        return bool(message.from_user and message.from_user.id in admins_list)

    return filters.create(check_if_admin, admins_list=admins_list)
