"""Tests for feedback bot ban module."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from feedback_bot.models import BannedUser, FeedbackChat, MessageMapping
from feedback_bot.telegram.feedback_bot.modules import ban as ban_module
from tests.feedback_bot.telegram.factories import build_message

pytestmark = [pytest.mark.asyncio, pytest.mark.django_db]


def _build_context(bot_config, *, args: list[str] | None = None):
    return SimpleNamespace(bot_data={'bot_config': bot_config}, args=args or [])


def _patch_reply_text(monkeypatch) -> AsyncMock:
    mock = AsyncMock()

    async def wrapper(self, *args, **kwargs):
        return await mock(self, *args, **kwargs)

    monkeypatch.setattr('telegram._message.Message.reply_text', wrapper)
    return mock


async def _prepare_mapping(bot_config, user_id: int, owner_message_id: int) -> None:
    chat, _ = await FeedbackChat.objects.aget_or_create(
        bot=bot_config,
        user_telegram_id=user_id,
        defaults={'username': ''},
    )
    await MessageMapping.objects.aupdate_or_create(
        bot=bot_config,
        user_message_id=1,
        defaults={'user_chat': chat, 'owner_message_id': owner_message_id},
    )


async def test_ban_user_from_reply(monkeypatch, feedback_app):
    _, bot_config = feedback_app
    await _prepare_mapping(bot_config, 999, 77)

    forwarded = build_message(
        bot_config.telegram_id,
        message_id=77,
        chat_id=bot_config.owner_id,
        chat_type='private',
        is_bot=True,
    )
    command_message = build_message(
        bot_config.owner_id,
        message_id=88,
        text='/ban',
        chat_id=bot_config.owner_id,
        chat_type='private',
        reply_to=forwarded,
    )
    update = SimpleNamespace(
        effective_message=command_message,
        effective_user=command_message.from_user,
    )

    reply_mock = _patch_reply_text(monkeypatch)

    context = _build_context(bot_config, args=['spammer'])
    await ban_module.ban_user(update, context)

    banned = (
        await BannedUser.objects.filter(bot=bot_config, user_telegram_id=999)
        .values_list('user_telegram_id', flat=True)
        .afirst()
    )
    assert banned == 999
    stored_reason = (
        await BannedUser.objects.filter(bot=bot_config, user_telegram_id=999)
        .values_list('reason', flat=True)
        .afirst()
    )
    assert stored_reason == 'spammer'

    assert reply_mock.await_count == 1
    args = reply_mock.await_args.args
    assert args[0] is command_message
    assert args[1] == 'User 999 banned.'


async def test_ban_user_from_args(monkeypatch, feedback_app):
    _, bot_config = feedback_app

    command_message = build_message(
        bot_config.owner_id,
        message_id=99,
        text='/ban 4242',
        chat_id=bot_config.owner_id,
        chat_type='private',
    )
    update = SimpleNamespace(
        effective_message=command_message,
        effective_user=command_message.from_user,
    )

    reply_mock = _patch_reply_text(monkeypatch)

    context = _build_context(bot_config, args=['4242', 'spam', 'links'])
    await ban_module.ban_user(update, context)

    banned = (
        await BannedUser.objects.filter(bot=bot_config, user_telegram_id=4242)
        .values_list('user_telegram_id', flat=True)
        .afirst()
    )
    assert banned == 4242
    stored_reason = (
        await BannedUser.objects.filter(bot=bot_config, user_telegram_id=4242)
        .values_list('reason', flat=True)
        .afirst()
    )
    assert stored_reason == 'spam links'

    assert reply_mock.await_count == 1
    args = reply_mock.await_args.args
    assert args[1] == 'User 4242 banned.'


async def test_ban_user_requires_target(monkeypatch, feedback_app):
    _, bot_config = feedback_app

    command_message = build_message(
        bot_config.owner_id,
        message_id=101,
        text='/ban',
        chat_id=bot_config.owner_id,
        chat_type='private',
    )
    update = SimpleNamespace(
        effective_message=command_message,
        effective_user=command_message.from_user,
    )

    reply_mock = _patch_reply_text(monkeypatch)

    context = _build_context(bot_config)
    await ban_module.ban_user(update, context)

    assert (
        await BannedUser.objects.filter(bot=bot_config)
        .values_list('user_telegram_id', flat=True)
        .afirst()
    ) is None
    assert reply_mock.await_count == 1
    assert (
        reply_mock.await_args.args[1] == 'Reply to a forwarded message or pass a numeric user ID.'
    )


async def test_unban_user(monkeypatch, feedback_app):
    _, bot_config = feedback_app
    await BannedUser.objects.aget_or_create(bot=bot_config, user_telegram_id=4242)

    command_message = build_message(
        bot_config.owner_id,
        message_id=111,
        text='/unban 4242',
        chat_id=bot_config.owner_id,
        chat_type='private',
    )
    update = SimpleNamespace(
        effective_message=command_message,
        effective_user=command_message.from_user,
    )

    reply_mock = _patch_reply_text(monkeypatch)

    context = _build_context(bot_config, args=['4242'])
    await ban_module.unban_user(update, context)

    assert (
        await BannedUser.objects.filter(bot=bot_config, user_telegram_id=4242)
        .values_list('user_telegram_id', flat=True)
        .afirst()
    ) is None
    assert reply_mock.await_count == 1
    assert reply_mock.await_args.args[1] == 'User 4242 unbanned.'


async def test_list_bans(monkeypatch, feedback_app):
    _, bot_config = feedback_app
    await BannedUser.objects.aget_or_create(
        bot=bot_config,
        user_telegram_id=111,
        defaults={'reason': 'spam'},
    )
    await BannedUser.objects.aget_or_create(
        bot=bot_config,
        user_telegram_id=222,
        defaults={'reason': ''},
    )

    command_message = build_message(
        bot_config.owner_id,
        message_id=211,
        text='/banned',
        chat_id=bot_config.owner_id,
        chat_type='private',
    )
    update = SimpleNamespace(
        effective_message=command_message,
        effective_user=command_message.from_user,
    )

    reply_mock = _patch_reply_text(monkeypatch)

    context = _build_context(bot_config)
    await ban_module.list_bans(update, context)

    assert reply_mock.await_count == 1
    payload = reply_mock.await_args.args[1]
    assert '111 - spam' in payload
    assert '222' in payload


async def test_non_owner_cannot_ban(monkeypatch, feedback_app):
    _, bot_config = feedback_app
    await _prepare_mapping(bot_config, 999, 90)

    forwarded = build_message(
        bot_config.telegram_id,
        message_id=90,
        chat_id=bot_config.owner_id,
        chat_type='private',
        is_bot=True,
    )
    command_message = build_message(
        555,
        message_id=91,
        text='/ban',
        chat_id=bot_config.owner_id,
        chat_type='private',
        reply_to=forwarded,
    )
    update = SimpleNamespace(
        effective_message=command_message,
        effective_user=command_message.from_user,
    )

    reply_mock = _patch_reply_text(monkeypatch)

    context = _build_context(bot_config)
    await ban_module.ban_user(update, context)

    assert (
        await BannedUser.objects.filter(bot=bot_config, user_telegram_id=999)
        .values_list('user_telegram_id', flat=True)
        .afirst()
    ) is None
    assert reply_mock.await_count == 0
