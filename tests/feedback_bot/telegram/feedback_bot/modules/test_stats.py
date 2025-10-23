"""Tests for feedback bot stats module."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from feedback_bot.models import BotStats, FeedbackChat
from tests.feedback_bot.telegram.factories import build_message, build_update

from telegram import MessageEntity, Update

pytestmark = [pytest.mark.ptb, pytest.mark.asyncio, pytest.mark.django_db]


def _patch_reply_html(monkeypatch) -> AsyncMock:
    mock = AsyncMock()

    async def wrapper(self, *args, **kwargs):
        return await mock(self, *args, **kwargs)

    monkeypatch.setattr('telegram._message.Message.reply_html', wrapper)
    return mock


async def test_stats_replies_with_counts(monkeypatch, feedback_app):
    app, bot_config = feedback_app
    await FeedbackChat.objects.aget_or_create(
        bot=bot_config,
        user_telegram_id=111,
        defaults={'username': ''},
    )
    await FeedbackChat.objects.aget_or_create(
        bot=bot_config,
        user_telegram_id=222,
        defaults={'username': ''},
    )

    stats_obj, _ = await BotStats.objects.aget_or_create(bot=bot_config)
    stats_obj.incoming_messages = 5
    stats_obj.outgoing_messages = 3
    await stats_obj.asave(update_fields=['incoming_messages', 'outgoing_messages'])

    command = build_message(
        bot_config.owner_id,
        message_id=10,
        text='/stats',
        chat_id=bot_config.owner_id,
        chat_type='private',
        entities=[MessageEntity(type='bot_command', offset=0, length=len('/stats'))],
    )
    update = Update.de_json(build_update(command).to_dict(), app.bot)
    assert update.effective_message is not None
    update.effective_message.set_bot(app.bot)

    reply_mock = _patch_reply_html(monkeypatch)

    await app.process_update(update)

    assert reply_mock.await_count == 1
    args = reply_mock.await_args.args
    assert args[0].message_id == 10
    assert (
        args[1] == '📈 <b>Bot statistics</b>\n\n'
        '👥 <b>Users</b>\n'
        '• 2 subscribers\n\n'
        '✍️ <b>Messages</b>\n'
        '• 5 inbound messages\n'
        '• 3 replies sent\n'
    )


async def test_stats_ignored_for_non_owner(monkeypatch, feedback_app):
    app, bot_config = feedback_app

    command = build_message(
        999,
        message_id=11,
        text='/stats',
        chat_id=bot_config.owner_id,
        chat_type='private',
        entities=[MessageEntity(type='bot_command', offset=0, length=len('/stats'))],
    )
    update = Update.de_json(build_update(command).to_dict(), app.bot)
    assert update.effective_message is not None
    update.effective_message.set_bot(app.bot)

    reply_mock = _patch_reply_html(monkeypatch)

    await app.process_update(update)

    assert reply_mock.await_count == 0
