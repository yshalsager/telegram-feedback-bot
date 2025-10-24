"""Integration tests for the builder broadcast command."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from feedback_bot.telegram.builder.modules import broadcast as broadcast_module
from tests.feedback_bot.telegram.factories import build_message, build_update

from telegram import MessageEntity, Update
from telegram.ext import ExtBot

pytestmark = [pytest.mark.ptb, pytest.mark.asyncio]

parametrize_broadcast = pytest.mark.parametrize(
    'app_with_handlers', ['feedback_bot.telegram.builder.modules.broadcast'], indirect=True
)


@parametrize_broadcast
async def test_broadcast_sends_to_targets(monkeypatch, app_with_handlers, ptb_send, ptb_errors):
    copy_mock = AsyncMock(
        side_effect=[SimpleNamespace(message_id=201), SimpleNamespace(message_id=202)]
    )
    monkeypatch.setattr(ExtBot, 'copy_message', copy_mock)

    targets_mock = AsyncMock(return_value=[222, 333])
    monkeypatch.setattr(broadcast_module, 'get_builder_broadcast_targets', targets_mock)

    record_mock = AsyncMock()
    monkeypatch.setattr(broadcast_module, 'record_broadcast_message', record_mock)

    sleep_mock = AsyncMock()
    monkeypatch.setattr('feedback_bot.telegram.utils.broadcast.sleep', sleep_mock)

    original = build_message(444, text='payload', message_id=99)
    command = build_message(
        111,
        text='/broadcast',
        message_id=100,
        reply_to=original,
        entities=[MessageEntity(type='bot_command', offset=0, length=len('/broadcast'))],
    )

    update_command = Update.de_json(build_update(command).to_dict(), app_with_handlers.bot)
    await app_with_handlers.process_update(update_command)

    assert targets_mock.await_count == 1
    assert targets_mock.await_args.args == (None,)
    assert copy_mock.await_count == 2
    first_call = copy_mock.await_args_list[0]
    assert first_call.kwargs['chat_id'] == 222
    assert first_call.kwargs['from_chat_id'] == original.chat_id
    assert first_call.kwargs['message_id'] == original.message_id

    second_call = copy_mock.await_args_list[1]
    assert second_call.kwargs['chat_id'] == 333

    assert record_mock.await_count == 2
    first_record = record_mock.await_args_list[0]
    assert first_record.args[:2] == (222, 201)
    assert first_record.kwargs['bot'] is None

    assert sleep_mock.await_count == 2

    assert ptb_send.await_count == 1
    assert ptb_send.await_args.kwargs['text'] == 'Broadcast completed: sent to 2 chats.'


@parametrize_broadcast
async def test_broadcast_reports_missing_targets(
    monkeypatch, app_with_handlers, ptb_send, ptb_errors
):
    monkeypatch.setattr(
        broadcast_module,
        'get_builder_broadcast_targets',
        AsyncMock(return_value=[]),
    )
    monkeypatch.setattr(ExtBot, 'copy_message', AsyncMock())
    monkeypatch.setattr('feedback_bot.telegram.utils.broadcast.sleep', AsyncMock())

    original = build_message(999, text='payload', message_id=11)
    command = build_message(
        111,
        text='/broadcast',
        message_id=12,
        reply_to=original,
        entities=[MessageEntity(type='bot_command', offset=0, length=len('/broadcast'))],
    )

    update_command = Update.de_json(build_update(command).to_dict(), app_with_handlers.bot)
    await app_with_handlers.process_update(update_command)

    assert ptb_send.await_count == 1
    assert ptb_send.await_args.kwargs['text'] == 'No recipients to broadcast to.'


@parametrize_broadcast
async def test_broadcast_passes_filters(monkeypatch, app_with_handlers, ptb_send, ptb_errors):
    monkeypatch.setattr(ExtBot, 'copy_message', AsyncMock())
    monkeypatch.setattr('feedback_bot.telegram.utils.broadcast.sleep', AsyncMock())

    targets_mock = AsyncMock(return_value=[])
    monkeypatch.setattr(broadcast_module, 'get_builder_broadcast_targets', targets_mock)

    original = build_message(444, text='payload', message_id=60)
    command = build_message(
        111,
        text='/broadcast\nsample_every 3\nusername_only yes',
        message_id=61,
        reply_to=original,
        entities=[MessageEntity(type='bot_command', offset=0, length=len('/broadcast'))],
    )

    update_command = Update.de_json(build_update(command).to_dict(), app_with_handlers.bot)
    await app_with_handlers.process_update(update_command)

    assert targets_mock.await_args.args == ({'sample_stride': 3, 'username_only': True},)
