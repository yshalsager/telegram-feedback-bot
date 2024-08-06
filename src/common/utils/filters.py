from collections.abc import Callable, Sequence
from typing import Any

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message

from src.common.utils.whitelist import get_whitelist, is_whitelisted


def is_admin(admins_list: Sequence[int]) -> filters.Filter:
    def check_if_admin(_: Callable[[Any], bool], __: Client, message: Message) -> bool:
        """Check if user is admin."""
        return bool(message.from_user and message.from_user.id in admins_list)

    return filters.create(check_if_admin, admins_list=admins_list)


def is_whitelisted_user() -> filters.Filter:
    def check_if_whitelisted(
        _: Callable[[Any], bool], __: Client, update: Message | CallbackQuery
    ) -> bool:
        """Check if user is whitelisted or if whitelist is empty."""
        whitelist = get_whitelist()
        if not whitelist:
            return True  # Allow all if whitelist is empty
        return bool(update.from_user and is_whitelisted(update.from_user.id))

    return filters.create(check_if_whitelisted)
