"""Tests for the builder bot application wiring."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from feedback_bot.telegram.utils.errors import report_error

pytestmark = pytest.mark.ptb


@pytest.mark.asyncio
async def test_report_error_sends_message(settings):
    settings.TELEGRAM_ADMIN_CHAT_ID = '-123'
    settings.TELEGRAM_LOG_TOPIC_ID = '42'
    update = SimpleNamespace(to_dict=lambda: {'foo': 'bar'})
    context = SimpleNamespace(error=RuntimeError('boom'), bot=AsyncMock())

    await report_error(update, context)

    assert context.bot.send_message.await_count == 1
    await_args = context.bot.send_message.await_args
    assert await_args.args == ()
    assert await_args.kwargs['chat_id'] == '-123'
    assert await_args.kwargs['message_thread_id'] == 42
    assert await_args.kwargs['parse_mode'] == 'HTML'
    text = await_args.kwargs['text']
    assert '<code>' in text
    assert 'RuntimeError' in text
    assert '<pre>' in text


@pytest.mark.asyncio
async def test_report_error_skips_without_admin_chat(settings):
    settings.TELEGRAM_ADMIN_CHAT_ID = ''
    settings.TELEGRAM_LOG_TOPIC_ID = '42'
    context = SimpleNamespace(error=RuntimeError('boom'), bot=AsyncMock())

    await report_error(None, context)

    assert context.bot.send_message.await_count == 0


@pytest.mark.asyncio
async def test_report_error_splits_long_messages(settings):
    settings.TELEGRAM_ADMIN_CHAT_ID = '-123'
    settings.TELEGRAM_LOG_TOPIC_ID = '42'
    long_error = 'x' * 5000
    update = SimpleNamespace(to_dict=lambda: {'foo': 'bar'})
    context = SimpleNamespace(error=RuntimeError(long_error), bot=AsyncMock())

    await report_error(update, context)

    calls = context.bot.send_message.await_args_list
    assert len(calls) >= 2
    for call in calls:
        kwargs = call.kwargs
        assert kwargs['chat_id'] == '-123'
        assert kwargs['message_thread_id'] == 42
        assert kwargs['parse_mode'] == 'HTML'
        assert len(kwargs['text']) <= 4096
    assert 'Exception raised while handling an update' in calls[0].kwargs['text']
    assert any('RuntimeError' in call.kwargs['text'] for call in calls)
