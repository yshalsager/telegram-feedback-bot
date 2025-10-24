"""Reusable PTB fixtures for feedback bot modules."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest
import pytest_asyncio
from feedback_bot.models import BannedUser, Bot, BotStats, FeedbackChat, User
from feedback_bot.telegram.feedback_bot import bot as feedback_bot_module
from feedback_bot.telegram.feedback_bot import modules as feedback_modules_pkg
from feedback_bot.utils.modules_loader import get_modules, load_modules
from tests.feedback_bot.telegram.factories import build_user

from telegram import Update
from telegram.ext import Application, ExtBot


@pytest.fixture(autouse=True)
def stub_translation_feedback(monkeypatch):
    """Replace `_` in feedback modules with identity for deterministic tests."""
    modules_path = Path(feedback_modules_pkg.__file__).parent
    loaded = load_modules(get_modules(modules_path))
    for module in loaded:
        monkeypatch.setattr(module, '_', lambda message: message, raising=False)


@pytest_asyncio.fixture
async def feedback_app(monkeypatch, db) -> tuple[Application, Bot]:
    """Initialize a PTB Application backed by a lightweight feedback bot config."""

    owner, _ = await User.objects.aget_or_create(
        telegram_id=5150,
        defaults={
            'username': 'owner',
            'language_code': 'en',
            'is_whitelisted': True,
            'is_admin': True,
        },
    )

    bot_config, created = await Bot.objects.aget_or_create(
        telegram_id=424242,
        defaults={
            'owner': owner,
            'name': 'FeedbackBot',
            'username': 'feedback_bot',
            'start_message': 'Hi',
            'feedback_received_message': 'Thanks',
        },
    )
    if created:
        bot_config.token = '0000000000:bbbbbbbbbbbbbbbbbbbb'  # noqa: S105
        await bot_config.asave()
    else:
        updates = {}
        if bot_config.feedback_received_message != 'Thanks':
            updates['feedback_received_message'] = 'Thanks'
        if bot_config.start_message != 'Hi':
            updates['start_message'] = 'Hi'
        if bot_config.communication_mode != Bot.CommunicationMode.STANDARD:
            updates['communication_mode'] = Bot.CommunicationMode.STANDARD
        if updates:
            await Bot.objects.filter(pk=bot_config.pk).aupdate(**updates)
            await bot_config.arefresh_from_db()
        else:
            await bot_config.arefresh_from_db()

    await BannedUser.objects.filter(bot=bot_config).adelete()
    await FeedbackChat.objects.filter(bot=bot_config).adelete()
    await BotStats.objects.filter(bot=bot_config).adelete()

    async def fake_initialize(self):  # type: ignore[no-redef]
        self._initialized = True
        self._bot_user = build_user(
            bot_config.telegram_id,
            first_name=bot_config.name,
            is_bot=True,
            username=bot_config.username,
        )

    monkeypatch.setattr(ExtBot, 'initialize', fake_initialize)

    app = feedback_bot_module.build_feedback_bot_application(bot_config)
    await app.initialize()
    return app, bot_config


@pytest.fixture
def make_group_update():
    """Factory to build a join Update for the feedback bot."""

    def _make(app: Application, chat_id: int, *, include_bot: bool) -> Update:
        members = [
            {
                'id': 999,
                'is_bot': False,
                'first_name': 'Person',
            }
        ]
        if include_bot:
            members.append(
                {
                    'id': app.bot.id,
                    'is_bot': True,
                    'first_name': 'FeedbackBot',
                }
            )

        payload = {
            'update_id': 1,
            'message': {
                'message_id': 10,
                'date': int(dt.datetime(2025, 1, 1, tzinfo=dt.UTC).timestamp()),
                'chat': {'id': chat_id, 'type': 'supergroup', 'title': 'Feedback Space'},
                'from': {'id': 888, 'is_bot': False, 'first_name': 'Admin'},
                'new_chat_members': members,
            },
        }

        update = Update.de_json(payload, app.bot)
        assert update.effective_message is not None
        update.effective_message.set_bot(app.bot)
        return update

    return _make


@pytest.fixture
def make_leave_update():
    """Factory to build a leave Update for the feedback bot."""

    def _make(app: Application, chat_id: int, *, include_bot: bool) -> Update:
        left_member = (
            {
                'id': app.bot.id,
                'is_bot': True,
                'first_name': 'FeedbackBot',
            }
            if include_bot
            else {
                'id': 333,
                'is_bot': False,
                'first_name': 'Random',
            }
        )

        payload = {
            'update_id': 2,
            'message': {
                'message_id': 20,
                'date': int(dt.datetime(2025, 1, 1, tzinfo=dt.UTC).timestamp()),
                'chat': {'id': chat_id, 'type': 'supergroup', 'title': 'Feedback Space'},
                'from': {'id': 777, 'is_bot': False, 'first_name': 'Admin'},
                'left_chat_member': left_member,
            },
        }

        update = Update.de_json(payload, app.bot)
        assert update.effective_message is not None
        update.effective_message.set_bot(app.bot)
        return update

    return _make
