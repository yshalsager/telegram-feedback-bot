"""Integration tests for the builder /update command."""

from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from feedback_bot.telegram.builder.modules import update as update_module
from tests.feedback_bot.telegram.factories import build_message

from telegram.ext import ExtBot

pytestmark = [pytest.mark.ptb, pytest.mark.asyncio]

parametrize_update = pytest.mark.parametrize(
    'app_with_handlers', ['feedback_bot.telegram.builder.modules.update'], indirect=True
)


@parametrize_update
async def test_update_happy_path(
    monkeypatch,
    settings,
    tmp_path,
    app_with_handlers,
    ptb_send,
    ptb_errors,
    make_command_update,
):
    settings.BASE_DIR = Path(tmp_path)

    outgoing = build_message(111, message_id=11, chat_id=999)
    outgoing.set_bot(app_with_handlers.bot)
    ptb_send.return_value = outgoing

    edit_mock = AsyncMock()
    monkeypatch.setattr(ExtBot, 'edit_message_text', edit_mock)

    restart_mock = AsyncMock()
    monkeypatch.setattr(update_module, 'restart', restart_mock)

    run_mock = AsyncMock(
        side_effect=[
            (0, 'django\n', ''),
            (0, '', ''),
            (0, 'HEAD is now at abc123\n', ''),
            (0, '', ''),
        ]
    )
    monkeypatch.setattr(update_module, '_run_command', run_mock)

    update = make_command_update(111, '/update')
    await app_with_handlers.process_update(update)

    assert run_mock.await_count == 4
    assert run_mock.await_args_list[0].args == (
        'git',
        'rev-parse',
        '--abbrev-ref',
        'HEAD',
    )
    assert run_mock.await_args_list[1].args == ('git', 'fetch', 'origin', 'django')
    assert run_mock.await_args_list[2].args == ('git', 'reset', '--hard', 'origin/django')
    assert run_mock.await_args_list[3].args == ('uv', 'sync')

    assert ptb_send.await_count == 1
    send_kwargs = ptb_send.await_args.kwargs
    assert send_kwargs['text'] == 'Updating, please wait...'

    assert edit_mock.await_count == 2
    first_edit = edit_mock.await_args_list[0].kwargs
    assert first_edit['text'] == (
        'Git update successful.\n<pre>HEAD is now at abc123</pre>\nSyncing dependencies...'
    )
    second_edit = edit_mock.await_args_list[1].kwargs
    assert second_edit['text'] == 'Update was successful. Restarting...'

    restart_mock.assert_awaited_once()
    called_update, called_context = restart_mock.await_args.args
    assert called_update is update
    assert called_context is not None


@parametrize_update
async def test_update_git_fetch_failure(
    monkeypatch,
    settings,
    tmp_path,
    app_with_handlers,
    ptb_send,
    ptb_errors,
    make_command_update,
):
    settings.BASE_DIR = Path(tmp_path)

    outgoing = build_message(111, message_id=11, chat_id=999)
    outgoing.set_bot(app_with_handlers.bot)
    ptb_send.return_value = outgoing

    edit_mock = AsyncMock()
    monkeypatch.setattr(ExtBot, 'edit_message_text', edit_mock)

    restart_mock = AsyncMock()
    monkeypatch.setattr(update_module, 'restart', restart_mock)

    run_mock = AsyncMock(side_effect=[(0, 'django\n', ''), (1, '', 'no permission')])
    monkeypatch.setattr(update_module, '_run_command', run_mock)

    update = make_command_update(111, '/update')
    await app_with_handlers.process_update(update)

    assert run_mock.await_count == 2
    assert edit_mock.await_count == 1
    error_kwargs = edit_mock.await_args.kwargs
    assert error_kwargs['text'] == 'Git fetch failed. Error: <pre>no permission</pre>'

    restart_mock.assert_not_awaited()
