"""Tests for group linking handlers."""

from unittest.mock import AsyncMock

import pytest
from feedback_bot.telegram.feedback_bot.modules import groups as groups_module

from telegram.ext import ExtBot

pytestmark = [pytest.mark.ptb, pytest.mark.asyncio]


async def test_link_bot_to_group(monkeypatch, feedback_app, make_group_update):
    app, bot_config = feedback_app
    assert app.bot_data['bot_config'] is bot_config

    link_mock = AsyncMock(return_value=True)
    monkeypatch.setattr(groups_module, 'update_bot_forward_chat_by_telegram_id', link_mock)

    update = make_group_update(app, -100222333, include_bot=True)
    reply_mock = AsyncMock()
    monkeypatch.setattr('telegram.Message.reply_text', reply_mock)
    await app.process_update(update)

    link_mock.assert_awaited_once_with(bot_config.telegram_id, -100222333)
    reply_mock.assert_awaited_once()
    call = reply_mock.await_args
    payload = call.kwargs.get('text') if call.kwargs else call.args[-1]
    assert 'Feedback' in payload


async def test_link_bot_ignores_other_new_members(monkeypatch, feedback_app, make_group_update):
    app, bot_config = feedback_app
    assert app.bot_data['bot_config'] is bot_config

    link_mock = AsyncMock(return_value=True)
    monkeypatch.setattr(groups_module, 'update_bot_forward_chat_by_telegram_id', link_mock)

    update = make_group_update(app, -100555666, include_bot=False)
    reply_mock = AsyncMock()
    monkeypatch.setattr('telegram.Message.reply_text', reply_mock)
    await app.process_update(update)

    assert link_mock.await_count == 0
    assert reply_mock.await_count == 0
    assert bot_config.forward_chat_id is None


async def test_unlink_bot_on_leave(monkeypatch, feedback_app, make_leave_update):
    app, bot_config = feedback_app
    assert app.bot_data['bot_config'] is bot_config
    bot_config.forward_chat_id = -100222333

    unlink_mock = AsyncMock(return_value=True)
    monkeypatch.setattr(groups_module, 'update_bot_forward_chat_by_telegram_id', unlink_mock)

    send_mock = AsyncMock()
    monkeypatch.setattr(ExtBot, 'send_message', send_mock)

    update = make_leave_update(app, -100222333, include_bot=True)
    await app.process_update(update)

    unlink_mock.assert_awaited_once_with(bot_config.telegram_id, None)
    send_mock.assert_awaited_once()
    call = send_mock.await_args
    assert call.args[0] == bot_config.owner_id
    assert 'FeedbackBot' in call.args[1]
    assert 'Feedback Space' in call.args[1]


async def test_unlink_bot_ignores_other_leave(monkeypatch, feedback_app, make_leave_update):
    app, bot_config = feedback_app
    assert app.bot_data['bot_config'] is bot_config
    bot_config.forward_chat_id = -100222333

    unlink_mock = AsyncMock(return_value=True)
    monkeypatch.setattr(groups_module, 'update_bot_forward_chat_by_telegram_id', unlink_mock)

    send_mock = AsyncMock()
    monkeypatch.setattr(ExtBot, 'send_message', send_mock)

    update = make_leave_update(app, -100222333, include_bot=False)
    await app.process_update(update)

    assert unlink_mock.await_count == 0
    assert send_mock.await_count == 0
    assert bot_config.forward_chat_id == -100222333
