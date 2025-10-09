"""Helpers for constructing telegram objects in tests."""

from __future__ import annotations

import datetime as dt
from types import SimpleNamespace
from unittest.mock import AsyncMock

from telegram import Chat, Message, MessageEntity, MessageOrigin, Update, User


def build_user(
    user_id: int, *, first_name: str = 'Tester', is_bot: bool = False, username: str | None = None
) -> User:
    return User(id=user_id, first_name=first_name, is_bot=is_bot, username=username)


def build_message(
    user_id: int,
    *,
    message_id: int = 1,
    text: str = 'payload',
    chat_id: int = 555,
    reply_to: Message | None = None,
    forward_origin: MessageOrigin | None = None,
    entities: list[MessageEntity] | None = None,
) -> Message:
    now = dt.datetime(2025, 1, 1, tzinfo=dt.UTC)
    return Message(
        message_id=message_id,
        date=now,
        chat=Chat(id=chat_id, type='private'),
        from_user=build_user(user_id),
        reply_to_message=reply_to,
        forward_origin=forward_origin,
        text=text,
        entities=entities,
    )


def build_update(message: Message, *, update_id: int = 1) -> Update:
    return Update(update_id=update_id, message=message)


def attach_send_message_mock(message: Message, *, response: Message | None = None):
    """Attach an AsyncMock send_message via Message.set_bot and return the mock."""
    send_mock = AsyncMock(return_value=response)
    message.set_bot(SimpleNamespace(send_message=send_mock))
    return send_mock
