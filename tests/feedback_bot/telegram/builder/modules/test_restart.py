"""Integration test for the restart handler via PTB Application.process_update."""

from pathlib import Path
from unittest.mock import Mock

import orjson
import pytest
from feedback_bot.telegram.builder.modules import restart as restart_module
from tests.feedback_bot.telegram.factories import build_message, build_update

from telegram import MessageEntity, Update

# Apply common marks to all tests in this module
pytestmark = [pytest.mark.ptb, pytest.mark.asyncio]

parametrize_restart = pytest.mark.parametrize(
    'app_with_handlers', ['feedback_bot.telegram.builder.modules.restart'], indirect=True
)


@parametrize_restart
async def test_restart_writes_restart_file_and_executes(
    monkeypatch, settings, tmp_path, app_with_handlers, ptb_send, ptb_errors
):
    settings.BASE_DIR = Path(tmp_path)

    # Incoming command from admin with a specific message_id
    incoming = build_message(
        111,
        message_id=10,
        text='/restart',
        chat_id=555,
        entities=[MessageEntity(type='bot_command', offset=0, length=len('/restart'))],
    )
    # The API returns a message representing the sent reply
    response = build_message(111, message_id=11, chat_id=999)
    ptb_send.return_value = response

    execlp_mock = Mock()
    monkeypatch.setattr(restart_module, 'execlp', execlp_mock)

    update = Update.de_json(build_update(incoming).to_dict(), app_with_handlers.bot)
    await app_with_handlers.process_update(update)

    ptb_send.assert_awaited_once()
    called = ptb_send.await_args.kwargs
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
