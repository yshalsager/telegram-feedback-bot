"""Tests for the /start handler using PTB objects."""

from unittest.mock import AsyncMock, Mock

import feedback_bot.telegram.builder.filters as filters_mod
import pytest
from feedback_bot.telegram.builder.modules import start as start_module
from tests.feedback_bot.telegram.factories import (
    attach_send_message_mock,
    build_message,
    build_update,
)

from telegram.ext import CallbackContext


@pytest.fixture(autouse=True)
def builder_settings(settings):
    settings.TELEGRAM_BUILDER_BOT_ADMINS = {111}
    settings.TELEGRAM_BUILDER_BOT_WEBHOOK_URL = 'https://builder.test'
    return settings


@pytest.fixture(autouse=True)
def stub_translation(monkeypatch):
    monkeypatch.setattr(start_module, '_', lambda key: key)


@pytest.mark.ptb
@pytest.mark.asyncio
async def test_start_sends_main_menu(monkeypatch):
    message = build_message(111)
    send_mock = attach_send_message_mock(message)

    create_user_mock = AsyncMock()
    monkeypatch.setattr(start_module, 'create_user', create_user_mock)
    monkeypatch.setattr(filters_mod, 'is_whitelisted_user', AsyncMock(return_value=True))

    update = build_update(message)
    context = CallbackContext(application=Mock())

    await start_module.start(update, context)

    create_user_mock.assert_awaited_once()
    payload = create_user_mock.await_args.args[0]
    assert payload == message.from_user.to_dict()

    send_mock.assert_awaited_once()
    called_kwargs = send_mock.await_args.kwargs
    assert called_kwargs['text'] == 'welcome'
    assert called_kwargs['chat_id'] == message.chat_id

    markup = called_kwargs['reply_markup']
    assert markup is not None
    assert len(markup.inline_keyboard) == 4

    first_button = markup.inline_keyboard[0][0]
    assert first_button.callback_data == 'add_bot'

    mini_app_button = markup.inline_keyboard[-1][0]
    assert mini_app_button.text == 'Open Mini App'
    assert mini_app_button.web_app.url == 'https://builder.test/'


@pytest.mark.ptb
@pytest.mark.asyncio
async def test_start_blocks_non_whitelisted_user(monkeypatch):
    message = build_message(999)
    send_mock = attach_send_message_mock(message)

    create_user_mock = AsyncMock()
    monkeypatch.setattr(start_module, 'create_user', create_user_mock)
    monkeypatch.setattr(filters_mod, 'is_whitelisted_user', AsyncMock(return_value=False))

    update = build_update(message)
    context = CallbackContext(application=Mock())

    result = await start_module.start(update, context)

    assert result is None
    assert create_user_mock.await_count == 0
    assert send_mock.await_count == 0
