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


def check_if_topic_reply(_: Callable[..., Any], __: Client, message: Message) -> bool:
    return bool(
        message.is_topic_message
        and message.reply_to_message
        and (
            message.reply_to_message.forward_sender_name
            or (
                message.reply_to_message.forward_from
                and message.reply_to_message.forward_from.full_name
            )
        )
    )


is_admin = filters.create(check_if_admin)
is_topic_reply = filters.create(check_if_topic_reply)
