"""Integration-style test driving PTB Application.process_update for /start."""

from unittest.mock import AsyncMock

import pytest
from feedback_bot.telegram.builder.modules import start as start_module

from telegram.ext import Application

# Apply common marks to all tests in this module
pytestmark = [pytest.mark.ptb, pytest.mark.asyncio]

parametrize_start = pytest.mark.parametrize(
    'app_with_handlers', ['feedback_bot.telegram.builder.modules.start'], indirect=True
)


@parametrize_start
async def test_start_integration_process_update(
    monkeypatch, app_with_handlers: Application, ptb_send, make_command_update, ptb_errors
):
    monkeypatch.setattr(
        'feedback_bot.telegram.builder.filters.is_whitelisted_user', AsyncMock(return_value=True)
    )
    create_user_mock = AsyncMock()
    monkeypatch.setattr(start_module, 'create_user', create_user_mock)

    update = make_command_update(111, '/start')
    await app_with_handlers.process_update(update)

    # Assertions: user creation and reply content
    create_user_mock.assert_awaited_once()
    payload = create_user_mock.await_args.args[0]
    assert payload['id'] == 111

    ptb_send.assert_awaited_once()
    called = ptb_send.await_args.kwargs
    assert called['chat_id'] == update.effective_message.chat_id
    assert called['text'] == 'welcome'
    assert called['reply_markup'] is not None

    # Quick sanity check for the keyboard content
    markup = called['reply_markup']
    assert len(markup.inline_keyboard) == 1
    assert markup.inline_keyboard[-1][0].web_app.url == 'https://builder.test/'


@parametrize_start
async def test_start_integration_blocks_non_whitelisted_user(
    monkeypatch, app_with_handlers: Application, ptb_send, make_command_update, ptb_errors
):
    monkeypatch.setattr(
        'feedback_bot.telegram.builder.filters.is_whitelisted_user', AsyncMock(return_value=False)
    )
    create_user_mock = AsyncMock()
    monkeypatch.setattr(start_module, 'create_user', create_user_mock)

    # Prepare update that matches the command handler for a non-whitelisted user
    update = make_command_update(999, '/start')
    await app_with_handlers.process_update(update)

    # Ensure no side-effects occurred
    assert create_user_mock.await_count == 0
    assert ptb_send.await_count == 0
