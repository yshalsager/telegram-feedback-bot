"""Reusable PTB integration fixtures for builder tests."""

from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
from pathlib import Path
from types import ModuleType
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from feedback_bot.telegram.builder import modules as builder_modules_pkg
from feedback_bot.utils.modules_loader import get_modules, load_modules
from tests.feedback_bot.telegram.factories import build_message, build_update, build_user

from telegram import MessageEntity, Update
from telegram.ext import Application, ExtBot


@pytest_asyncio.fixture
async def ptb_app(monkeypatch) -> Application:
    """Initialized Application without network calls and with a bot username.

    - Uses a dummy token
    - Sets updater(None)
    - Stubs ExtBot.initialize to avoid hitting the Bot API and assigns a bot user
    """

    async def fake_initialize(self):  # type: ignore[no-redef]
        self._initialized = True
        # Provide a username so CommandHandler can parse commands like '/start@username'
        self._bot_user = build_user(999, first_name='TestBot', is_bot=True, username='testbot')

    monkeypatch.setattr(ExtBot, 'initialize', fake_initialize)

    app = Application.builder().token('0000000000:aaaaaaaaaaaaaaaaaaaa').updater(None).build()
    await app.initialize()
    return app


@pytest.fixture
def ptb_send(monkeypatch):
    """Patch ExtBot.send_message with an AsyncMock and return it."""
    send_mock = AsyncMock()
    monkeypatch.setattr(ExtBot, 'send_message', send_mock)
    return send_mock


@pytest.fixture
def make_command_update(ptb_app: Application) -> Callable[[int, str], Update]:
    """Factory to construct a bot-bound Update for a given command text.

    Example: make_command_update(111, '/start')
    """

    def _make(user_id: int, text: str) -> Update:
        first_token = text.split()[0]
        entity = MessageEntity(type='bot_command', offset=0, length=len(first_token))
        msg = build_message(user_id, text=text, entities=[entity])
        upd = build_update(msg)
        return Update.de_json(upd.to_dict(), ptb_app.bot)

    return _make


@pytest.fixture(autouse=True)
def builder_settings(settings):
    """Default settings for builder tests to avoid repetition."""
    settings.TELEGRAM_BUILDER_BOT_ADMINS = {111}
    settings.TELEGRAM_BUILDER_BOT_WEBHOOK_URL = 'https://builder.test'
    return settings


@pytest.fixture(autouse=True)
def stub_translation_builder(monkeypatch, settings):
    """Stub i18n '_' across all builder modules dynamically.

    Mirrors how the real bot loads modules by discovering everything under
    `feedback_bot/telegram/builder/modules` and applying a stub for `_`.
    """
    modules_path = Path(builder_modules_pkg.__file__).parent
    loaded = load_modules(get_modules(modules_path))
    for mod in loaded:
        # Replace gettext alias `_` with identity for deterministic tests
        monkeypatch.setattr(mod, '_', lambda key: key, raising=False)


@pytest.fixture
def ptb_errors(ptb_app: Application):
    """Registers an error handler that collects exceptions and asserts none occurred.

    Use by including `ptb_errors` in your test signature. If any exception is raised
    inside PTB during update processing, the test will fail at teardown with the error.
    """
    captured: list[BaseException] = []

    async def on_error(_update, context):  # type: ignore[no-redef]
        captured.append(context.error)

    ptb_app.add_error_handler(on_error)
    try:
        yield captured
    finally:
        assert not captured, f'PTB errors captured during test: {captured!r}'


@pytest.fixture
def add_handlers(ptb_app: Application):
    """Factory that registers HANDLERS from given modules on the ptb_app and returns it."""

    def _add(*modules) -> Application:
        for mod in modules:
            handlers = getattr(mod, 'HANDLERS', [])
            for handler in handlers:
                ptb_app.add_handler(handler)
        return ptb_app

    return _add


@pytest.fixture
def app_with_handlers(add_handlers, request):
    """Parametrized fixture that returns an app with handlers from given modules.

    Accepts a dotted module path, a module object, or an iterable of either via
    pytest's indirect parametrization.

    Usage examples:
    - One module by dotted path:
        @pytest.mark.parametrize(
            'app_with_handlers',
            ['feedback_bot.telegram.builder.modules.start'],
            indirect=True,
        )
        def test_start_flow(app_with_handlers):
            app = app_with_handlers
            ...

    - Multiple modules:
        @pytest.mark.parametrize(
            'app_with_handlers',
            [[
                'feedback_bot.telegram.builder.modules.start',
                'feedback_bot.telegram.builder.modules.whitelist',
            ]],
            indirect=True,
        )
        def test_flow(app_with_handlers):
            app = app_with_handlers
            ...
    """

    modules_param = getattr(request, 'param', None)
    if modules_param is None:
        raise RuntimeError(
            'app_with_handlers fixture requires parameters. Use indirect parametrization.'
        )

    if not isinstance(modules_param, (list, tuple)):
        modules_param = [modules_param]

    modules: list[ModuleType] = []
    for m in modules_param:
        if isinstance(m, str):
            modules.append(import_module(m))
        else:
            modules.append(m)

    return add_handlers(*modules)
