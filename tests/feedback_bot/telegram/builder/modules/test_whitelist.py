"""Integration tests for whitelist handlers using PTB Application.process_update."""

import datetime as dt
from unittest.mock import AsyncMock

import pytest
from feedback_bot.telegram.builder.modules import whitelist as whitelist_module
from tests.feedback_bot.telegram.factories import build_message, build_update, build_user

from telegram import MessageEntity, MessageOriginHiddenUser, MessageOriginUser, Update

pytestmark = [pytest.mark.ptb, pytest.mark.asyncio]

parametrize_whitelist = pytest.mark.parametrize(
    'app_with_handlers', ['feedback_bot.telegram.builder.modules.whitelist'], indirect=True
)


@parametrize_whitelist
async def test_whitelist_user_from_reply_adds_visible_user(
    monkeypatch, app_with_handlers, ptb_send, ptb_errors
):
    forwarder = build_message(
        444,
        forward_origin=MessageOriginUser(
            dt.datetime(2025, 1, 1, tzinfo=dt.UTC),
            sender_user=build_user(222, first_name='Origin'),
        ),
    )
    # Admin replies with '/whitelist' to the forwarded message
    reply = build_message(
        111,
        text='/whitelist',
        reply_to=forwarder,
        entities=[MessageEntity(type='bot_command', offset=0, length=len('/whitelist'))],
    )

    create_user_mock = AsyncMock()
    monkeypatch.setattr(whitelist_module, 'create_user', create_user_mock)

    update = Update.de_json(build_update(reply).to_dict(), app_with_handlers.bot)
    await app_with_handlers.process_update(update)

    create_user_mock.assert_awaited_once()
    payload = create_user_mock.await_args.args[0]
    assert payload == forwarder.forward_origin.sender_user.to_dict()

    ptb_send.assert_awaited_once()
    assert ptb_send.await_args.kwargs['text'] == 'user_whitelisted'


@parametrize_whitelist
async def test_whitelist_user_from_reply_rejects_hidden_user(
    monkeypatch, app_with_handlers, ptb_send, ptb_errors
):
    forwarder = build_message(
        444,
        forward_origin=MessageOriginHiddenUser(
            dt.datetime(2025, 1, 1, tzinfo=dt.UTC),
            sender_user_name='Anonymous',
        ),
    )
    reply = build_message(
        111,
        text='/whitelist',
        reply_to=forwarder,
        entities=[MessageEntity(type='bot_command', offset=0, length=len('/whitelist'))],
    )

    create_user_mock = AsyncMock()
    monkeypatch.setattr(whitelist_module, 'create_user', create_user_mock)

    update = Update.de_json(build_update(reply).to_dict(), app_with_handlers.bot)
    await app_with_handlers.process_update(update)

    assert create_user_mock.await_count == 0
    ptb_send.assert_awaited_once()
    assert ptb_send.await_args.kwargs['text'] == 'cant_whitelist_hidden_user'


@parametrize_whitelist
async def test_whitelist_user_from_id_uses_context_match(
    monkeypatch, app_with_handlers, ptb_send, ptb_errors
):
    create_user_mock = AsyncMock()
    monkeypatch.setattr(whitelist_module, 'create_user', create_user_mock)

    update = Update.de_json(
        build_update(
            build_message(
                111,
                text='/whitelist 321',
                entities=[MessageEntity(type='bot_command', offset=0, length=len('/whitelist'))],
            )
        ).to_dict(),
        app_with_handlers.bot,
    )

    await app_with_handlers.process_update(update)

    create_user_mock.assert_awaited_once_with({'id': 321})
    ptb_send.assert_awaited_once()
    assert ptb_send.await_args.kwargs['text'] == 'user_whitelisted'
