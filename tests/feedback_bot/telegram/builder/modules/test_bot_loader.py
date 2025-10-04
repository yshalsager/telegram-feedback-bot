"""Tests for the builder bot loader logic."""

from types import SimpleNamespace

import pytest
from feedback_bot.telegram.builder import bot as bot_module

from telegram import Update
from telegram.ext import CallbackContext, CommandHandler


@pytest.mark.ptb
def test_load_builder_modules_registers_handlers(monkeypatch):
    added_handlers = []

    class DummyApp:
        def add_handler(self, handler: CommandHandler):
            added_handlers.append(handler)

    async def dummy(update: Update, context: CallbackContext) -> None:
        "Doc string"
        return

    handler = CommandHandler('foo', dummy)
    test_module = SimpleNamespace(HANDLERS=[handler])

    monkeypatch.setattr(bot_module, 'ptb_application', DummyApp())
    monkeypatch.setattr(bot_module, 'load_modules', lambda modules: [test_module])

    commands = bot_module.load_builder_modules()

    assert added_handlers == [handler]
    assert [(cmd.command, cmd.description) for cmd in commands] == [('foo', 'Doc string')]


@pytest.mark.ptb
def test_load_builder_modules_skips_non_command_handlers(monkeypatch):
    added_handlers = []

    class DummyApp:
        def add_handler(self, handler):
            added_handlers.append(handler)

    non_command_handler = SimpleNamespace()
    test_module = SimpleNamespace(HANDLERS=[non_command_handler])

    monkeypatch.setattr(bot_module, 'ptb_application', DummyApp())
    monkeypatch.setattr(bot_module, 'load_modules', lambda modules: [test_module])

    commands = bot_module.load_builder_modules()

    assert added_handlers == [non_command_handler]
    assert commands == []
