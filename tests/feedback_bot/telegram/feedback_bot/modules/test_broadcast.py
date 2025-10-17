"""Tests for the feedback bot broadcast command."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from feedback_bot.telegram.feedback_bot.modules import broadcast as broadcast_module
from tests.feedback_bot.telegram.factories import build_message, build_update

from telegram import MessageEntity, Update
from telegram.ext import ExtBot

pytestmark = [pytest.mark.ptb, pytest.mark.asyncio]


async def _process_broadcast(app, command):
    update = Update.de_json(build_update(command).to_dict(), app.bot)
    await app.process_update(update)


async def test_owner_broadcasts_to_all(monkeypatch, feedback_app):
    app, bot_config = feedback_app
    bot_config.id = 42

    copy_mock = AsyncMock(
        side_effect=[SimpleNamespace(message_id=310), SimpleNamespace(message_id=311)]
    )
    monkeypatch.setattr(ExtBot, 'copy_message', copy_mock)

    targets_mock = AsyncMock(return_value=[777, 888])
    monkeypatch.setattr(broadcast_module, 'get_feedback_chat_targets', targets_mock)

    record_mock = AsyncMock()
    monkeypatch.setattr(broadcast_module, 'record_broadcast_message', record_mock)

    sleep_mock = AsyncMock()
    monkeypatch.setattr('feedback_bot.telegram.utils.broadcast.sleep', sleep_mock)

    send_mock = AsyncMock()
    monkeypatch.setattr(ExtBot, 'send_message', send_mock)

    original = build_message(bot_config.owner_id, text='announcement', message_id=50)
    command = build_message(
        bot_config.owner_id,
        text='/broadcast',
        message_id=51,
        reply_to=original,
        entities=[MessageEntity(type='bot_command', offset=0, length=len('/broadcast'))],
    )

    await _process_broadcast(app, command)

    expected_reference = broadcast_module._resolve_bot_reference(bot_config)
    targets_mock.assert_awaited_once_with(expected_reference)
    assert copy_mock.await_count == 2
    first_call = copy_mock.await_args_list[0]
    assert first_call.kwargs['chat_id'] == 777
    assert first_call.kwargs['from_chat_id'] == original.chat_id

    assert record_mock.await_count == 2
    first_record = record_mock.await_args_list[0]
    assert first_record.args[:2] == (777, 310)
    assert first_record.kwargs['bot'] == expected_reference

    assert sleep_mock.await_count == 2

    send_mock.assert_awaited_once()
    assert send_mock.await_args.kwargs['text'] == 'Broadcast completed: sent to 2 chats.'


async def test_broadcast_ignores_non_owner(monkeypatch, feedback_app):
    app, bot_config = feedback_app
    bot_config.id = 77

    copy_mock = AsyncMock()
    monkeypatch.setattr(ExtBot, 'copy_message', copy_mock)
    monkeypatch.setattr(broadcast_module, 'get_feedback_chat_targets', AsyncMock())
    monkeypatch.setattr(broadcast_module, 'record_broadcast_message', AsyncMock())
    monkeypatch.setattr('feedback_bot.telegram.utils.broadcast.sleep', AsyncMock())
    send_mock = AsyncMock()
    monkeypatch.setattr(ExtBot, 'send_message', send_mock)

    original = build_message(300, text='announcement', message_id=70)
    command = build_message(
        300,
        text='/broadcast',
        message_id=71,
        reply_to=original,
        entities=[MessageEntity(type='bot_command', offset=0, length=len('/broadcast'))],
    )

    await _process_broadcast(app, command)

    assert copy_mock.await_count == 0
    assert send_mock.await_count == 0


async def test_broadcast_reports_when_no_targets(monkeypatch, feedback_app):
    app, bot_config = feedback_app
    bot_config.id = 13

    monkeypatch.setattr(ExtBot, 'copy_message', AsyncMock())
    monkeypatch.setattr('feedback_bot.telegram.utils.broadcast.sleep', AsyncMock())
    monkeypatch.setattr(
        broadcast_module,
        'get_feedback_chat_targets',
        AsyncMock(return_value=[]),
    )
    send_mock = AsyncMock()
    monkeypatch.setattr(ExtBot, 'send_message', send_mock)

    original = build_message(bot_config.owner_id, text='announcement', message_id=90)
    command = build_message(
        bot_config.owner_id,
        text='/broadcast',
        message_id=91,
        reply_to=original,
        entities=[MessageEntity(type='bot_command', offset=0, length=len('/broadcast'))],
    )

    await _process_broadcast(app, command)

    send_mock.assert_awaited_once()
    assert send_mock.await_args.kwargs['text'] == 'No subscribers to broadcast to.'
