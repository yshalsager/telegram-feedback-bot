"""Tests for the restart handler using PTB objects."""

from pathlib import Path
from unittest.mock import Mock

import orjson
import pytest
from feedback_bot.telegram.builder.modules import restart as restart_module
from tests.feedback_bot.telegram.factories import (
    attach_send_message_mock,
    build_message,
    build_update,
)


@pytest.mark.ptb
@pytest.mark.asyncio
async def test_restart_writes_restart_file_and_executes(monkeypatch, settings, tmp_path):
    settings.BASE_DIR = Path(tmp_path)

    incoming = build_message(555, message_id=10)
    response = build_message(555, message_id=11, chat_id=999)

    send_mock = attach_send_message_mock(incoming, response=response)

    execlp_mock = Mock()
    monkeypatch.setattr(restart_module, 'execlp', execlp_mock)

    update = build_update(incoming)

    await restart_module.restart(update, Mock())

    send_mock.assert_awaited_once()
    called = send_mock.await_args.kwargs
    assert called['text'] == 'Restarting, please wait...'
    assert called['chat_id'] == incoming.chat_id
    assert called['reply_parameters'].message_id == 10

    restart_file = settings.BASE_DIR / 'restart.json'
    assert restart_file.exists()
    data = orjson.loads(restart_file.read_bytes())
    assert data == {'chat': response.chat_id, 'message': response.message_id}

    execlp_mock.assert_called_once_with(
        'uv',
        'uv',
        'run',
        'granian',
        '--interface',
        'asgi',
        'config.asgi:application',
    )
