"""Tests for whitelist handlers using PTB primitives."""

import datetime as dt
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import regex as re
from feedback_bot.telegram.builder.modules import whitelist as whitelist_module
from tests.feedback_bot.telegram.factories import (
    attach_send_message_mock,
    build_message,
    build_update,
    build_user,
)

from telegram import MessageOriginHiddenUser, MessageOriginUser


@pytest.fixture(autouse=True)
def stub_translation(monkeypatch):
    monkeypatch.setattr(whitelist_module, '_', lambda key: key)


@pytest.mark.ptb
@pytest.mark.asyncio
async def test_whitelist_user_from_reply_adds_visible_user(monkeypatch):
    forwarder = build_message(
        444,
        forward_origin=MessageOriginUser(
            dt.datetime(2025, 1, 1, tzinfo=dt.UTC),
            sender_user=build_user(222, first_name='Origin'),
        ),
    )
    message = build_message(111, reply_to=forwarder)
    send_mock = attach_send_message_mock(message)

    create_user_mock = AsyncMock()
    monkeypatch.setattr(whitelist_module, 'create_user', create_user_mock)

    update = build_update(message)

    await whitelist_module.whitelist_user_from_reply(update, SimpleNamespace())

    create_user_mock.assert_awaited_once()
    payload = create_user_mock.await_args.args[0]
    assert payload == forwarder.forward_origin.sender_user.to_dict()

    send_mock.assert_awaited_once()
    assert send_mock.await_args.kwargs['text'] == 'user_whitelisted'


@pytest.mark.ptb
@pytest.mark.asyncio
async def test_whitelist_user_from_reply_rejects_hidden_user(monkeypatch):
    forwarder = build_message(
        444,
        forward_origin=MessageOriginHiddenUser(
            dt.datetime(2025, 1, 1, tzinfo=dt.UTC),
            sender_user_name='Anonymous',
        ),
    )
    message = build_message(111, reply_to=forwarder)
    send_mock = attach_send_message_mock(message)

    create_user_mock = AsyncMock()
    monkeypatch.setattr(whitelist_module, 'create_user', create_user_mock)

    update = build_update(message)

    await whitelist_module.whitelist_user_from_reply(update, SimpleNamespace())

    assert create_user_mock.await_count == 0
    send_mock.assert_awaited_once()
    assert send_mock.await_args.kwargs['text'] == 'cant_whitelist_hidden_user'


@pytest.mark.ptb
@pytest.mark.asyncio
async def test_whitelist_user_from_id_uses_context_match(monkeypatch):
    message = build_message(111)
    send_mock = attach_send_message_mock(message)

    create_user_mock = AsyncMock()
    monkeypatch.setattr(whitelist_module, 'create_user', create_user_mock)

    update = build_update(message)
    match = re.match(r'^/whitelist\s+(\d+)$', '/whitelist 321')
    context = SimpleNamespace(matches=[match])

    await whitelist_module.whitelist_user_from_id(update, context)

    create_user_mock.assert_awaited_once_with({'id': 321})
    send_mock.assert_awaited_once()
    assert send_mock.await_args.kwargs['text'] == 'user_whitelisted'
