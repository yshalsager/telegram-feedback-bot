"""Tests for feedback bot delete module."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from feedback_bot.models import FeedbackChat, MessageMapping
from feedback_bot.telegram.feedback_bot.modules import delete as delete_module
from tests.feedback_bot.telegram.factories import build_message

from telegram.error import BadRequest, Forbidden

pytestmark = [pytest.mark.asyncio, pytest.mark.django_db]


def _build_context(bot_config, delete_mock):
    return SimpleNamespace(
        bot_data={'bot_config': bot_config},
        bot=SimpleNamespace(delete_message=delete_mock),
    )


def _patch_reply_text(monkeypatch) -> AsyncMock:
    mock = AsyncMock()

    async def wrapper(self, *args, **kwargs):
        return await mock(self, *args, **kwargs)

    monkeypatch.setattr('telegram._message.Message.reply_text', wrapper)
    return mock


async def _prepare_mapping(
    bot_config, user_id: int, owner_message_id: int, user_message_id: int
) -> None:
    chat, _ = await FeedbackChat.objects.aget_or_create(
        bot=bot_config,
        user_telegram_id=user_id,
        defaults={'username': ''},
    )
    await MessageMapping.objects.aupdate_or_create(
        bot=bot_config,
        user_message_id=user_message_id,
        defaults={'user_chat': chat, 'owner_message_id': owner_message_id},
    )


async def test_delete_feedback_removes_messages(feedback_app):
    _, bot_config = feedback_app
    await FeedbackChat.objects.filter(bot=bot_config).adelete()
    await MessageMapping.objects.filter(bot=bot_config).adelete()
    await _prepare_mapping(bot_config, 999, 77, 11)

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
        text='/delete',
        chat_id=bot_config.owner_id,
        chat_type='private',
        reply_to=forwarded,
    )
    update = SimpleNamespace(
        effective_message=command_message,
        effective_user=command_message.from_user,
    )

    delete_mock = AsyncMock(return_value=True)
    context = _build_context(bot_config, delete_mock)

    await delete_module.delete_feedback(update, context)

    assert delete_mock.await_count == 3
    owner_call = delete_mock.await_args_list[0].kwargs
    assert owner_call == {'chat_id': bot_config.owner_id, 'message_id': 77}
    user_call = delete_mock.await_args_list[1].kwargs
    assert user_call == {'chat_id': 999, 'message_id': 11}
    command_call = delete_mock.await_args_list[2].kwargs
    assert command_call == {'chat_id': bot_config.owner_id, 'message_id': 88}

    remaining = await MessageMapping.objects.filter(bot=bot_config).acount()
    assert remaining == 0


async def test_delete_feedback_requires_mapping(monkeypatch, feedback_app):
    _, bot_config = feedback_app
    await FeedbackChat.objects.filter(bot=bot_config).adelete()
    await MessageMapping.objects.filter(bot=bot_config).adelete()

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
        text='/delete',
        chat_id=bot_config.owner_id,
        chat_type='private',
        reply_to=forwarded,
    )
    update = SimpleNamespace(
        effective_message=command_message,
        effective_user=command_message.from_user,
    )

    reply_mock = _patch_reply_text(monkeypatch)

    delete_mock = AsyncMock()
    context = _build_context(bot_config, delete_mock)

    await delete_module.delete_feedback(update, context)

    assert reply_mock.await_count == 1
    args = reply_mock.await_args.args
    assert args[0] is command_message
    assert args[1] == 'Nothing to delete.'
    assert delete_mock.await_count == 0


async def test_delete_feedback_reports_failure(monkeypatch, feedback_app):
    _, bot_config = feedback_app
    await FeedbackChat.objects.filter(bot=bot_config).adelete()
    await MessageMapping.objects.filter(bot=bot_config).adelete()
    await _prepare_mapping(bot_config, 999, 77, 11)

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
        text='/delete',
        chat_id=bot_config.owner_id,
        chat_type='private',
        reply_to=forwarded,
    )
    update = SimpleNamespace(
        effective_message=command_message,
        effective_user=command_message.from_user,
    )

    reply_mock = _patch_reply_text(monkeypatch)

    delete_mock = AsyncMock(
        side_effect=[BadRequest("Message can't be deleted"), BadRequest("Message can't be deleted")]
    )
    context = _build_context(bot_config, delete_mock)

    await delete_module.delete_feedback(update, context)

    assert delete_mock.await_count == 2
    assert reply_mock.await_count == 1
    args = reply_mock.await_args.args
    assert args[1] == 'Could not delete the message.'

    remaining = await MessageMapping.objects.filter(bot=bot_config).acount()
    assert remaining == 1


async def test_clear_feedback_removes_all_messages(feedback_app):
    _, bot_config = feedback_app
    await FeedbackChat.objects.filter(bot=bot_config).adelete()
    await MessageMapping.objects.filter(bot=bot_config).adelete()
    await _prepare_mapping(bot_config, 999, 77, 11)
    await _prepare_mapping(bot_config, 999, 78, 12)

    forwarded = build_message(
        bot_config.telegram_id,
        message_id=77,
        chat_id=bot_config.owner_id,
        chat_type='private',
        is_bot=True,
    )
    command_message = build_message(
        bot_config.owner_id,
        message_id=99,
        text='/clear',
        chat_id=bot_config.owner_id,
        chat_type='private',
        reply_to=forwarded,
    )
    update = SimpleNamespace(
        effective_message=command_message,
        effective_user=command_message.from_user,
    )

    delete_mock = AsyncMock(return_value=True)
    context = _build_context(bot_config, delete_mock)

    await delete_module.clear_feedback(update, context)

    expected_calls = [
        {'chat_id': bot_config.owner_id, 'message_id': 77},
        {'chat_id': bot_config.owner_id, 'message_id': 78},
        {'chat_id': 999, 'message_id': 11},
        {'chat_id': 999, 'message_id': 12},
        {'chat_id': bot_config.owner_id, 'message_id': 99},
    ]
    assert delete_mock.await_count == len(expected_calls)
    actual_calls = [call.kwargs for call in delete_mock.await_args_list]
    assert actual_calls == expected_calls

    remaining = await MessageMapping.objects.filter(bot=bot_config).acount()
    assert remaining == 0


async def test_clear_feedback_ignores_deactivated_user(feedback_app):
    _, bot_config = feedback_app
    await FeedbackChat.objects.filter(bot=bot_config).adelete()
    await MessageMapping.objects.filter(bot=bot_config).adelete()
    await _prepare_mapping(bot_config, 999, 77, 11)
    await _prepare_mapping(bot_config, 999, 78, 12)

    forwarded = build_message(
        bot_config.telegram_id,
        message_id=77,
        chat_id=bot_config.owner_id,
        chat_type='private',
        is_bot=True,
    )
    command_message = build_message(
        bot_config.owner_id,
        message_id=99,
        text='/clear',
        chat_id=bot_config.owner_id,
        chat_type='private',
        reply_to=forwarded,
    )
    update = SimpleNamespace(
        effective_message=command_message,
        effective_user=command_message.from_user,
    )

    delete_mock = AsyncMock(
        side_effect=[
            True,
            True,
            Forbidden('Forbidden: user is deactivated'),
            True,
            True,
        ]
    )
    context = _build_context(bot_config, delete_mock)

    await delete_module.clear_feedback(update, context)

    assert delete_mock.await_count == 5
    remaining = await MessageMapping.objects.filter(bot=bot_config).acount()
    assert remaining == 0


async def test_clear_feedback_requires_mapping(monkeypatch, feedback_app):
    _, bot_config = feedback_app
    await FeedbackChat.objects.filter(bot=bot_config).adelete()
    await MessageMapping.objects.filter(bot=bot_config).adelete()

    forwarded = build_message(
        bot_config.telegram_id,
        message_id=77,
        chat_id=bot_config.owner_id,
        chat_type='private',
        is_bot=True,
    )
    command_message = build_message(
        bot_config.owner_id,
        message_id=99,
        text='/clear',
        chat_id=bot_config.owner_id,
        chat_type='private',
        reply_to=forwarded,
    )
    update = SimpleNamespace(
        effective_message=command_message,
        effective_user=command_message.from_user,
    )

    reply_mock = _patch_reply_text(monkeypatch)
    delete_mock = AsyncMock()
    context = _build_context(bot_config, delete_mock)

    await delete_module.clear_feedback(update, context)

    assert reply_mock.await_count == 1
    args = reply_mock.await_args.args
    assert args[1] == 'Nothing to clear.'
    assert delete_mock.await_count == 0


async def test_clear_feedback_reports_failure(monkeypatch, feedback_app):
    _, bot_config = feedback_app
    await FeedbackChat.objects.filter(bot=bot_config).adelete()
    await MessageMapping.objects.filter(bot=bot_config).adelete()
    await _prepare_mapping(bot_config, 999, 77, 11)

    forwarded = build_message(
        bot_config.telegram_id,
        message_id=77,
        chat_id=bot_config.owner_id,
        chat_type='private',
        is_bot=True,
    )
    command_message = build_message(
        bot_config.owner_id,
        message_id=99,
        text='/clear',
        chat_id=bot_config.owner_id,
        chat_type='private',
        reply_to=forwarded,
    )
    update = SimpleNamespace(
        effective_message=command_message,
        effective_user=command_message.from_user,
    )

    reply_mock = _patch_reply_text(monkeypatch)
    delete_mock = AsyncMock(
        side_effect=[BadRequest("Message can't be deleted"), BadRequest("Message can't be deleted")]
    )
    context = _build_context(bot_config, delete_mock)

    await delete_module.clear_feedback(update, context)

    assert delete_mock.await_count == 2
    assert reply_mock.await_count == 1
    args = reply_mock.await_args.args
    assert args[1] == 'Could not clear messages.'

    remaining = await MessageMapping.objects.filter(bot=bot_config).acount()
    assert remaining == 1


async def test_clear_feedback_trims_from_replied_message(feedback_app):
    _, bot_config = feedback_app
    await FeedbackChat.objects.filter(bot=bot_config).adelete()
    await MessageMapping.objects.filter(bot=bot_config).adelete()
    await _prepare_mapping(bot_config, 999, 77, 11)
    await _prepare_mapping(bot_config, 999, 78, 12)
    await _prepare_mapping(bot_config, 999, 79, 13)

    forwarded = build_message(
        bot_config.telegram_id,
        message_id=78,
        chat_id=bot_config.owner_id,
        chat_type='private',
        is_bot=True,
    )
    command_message = build_message(
        bot_config.owner_id,
        message_id=120,
        text='/clear',
        chat_id=bot_config.owner_id,
        chat_type='private',
        reply_to=forwarded,
    )
    update = SimpleNamespace(
        effective_message=command_message,
        effective_user=command_message.from_user,
    )

    delete_mock = AsyncMock(return_value=True)
    context = _build_context(bot_config, delete_mock)

    await delete_module.clear_feedback(update, context)

    expected_calls = [
        {'chat_id': bot_config.owner_id, 'message_id': 78},
        {'chat_id': bot_config.owner_id, 'message_id': 79},
        {'chat_id': 999, 'message_id': 12},
        {'chat_id': 999, 'message_id': 13},
        {'chat_id': bot_config.owner_id, 'message_id': 120},
    ]
    assert delete_mock.await_count == len(expected_calls)
    actual_calls = [call.kwargs for call in delete_mock.await_args_list]
    assert actual_calls == expected_calls

    remaining = await MessageMapping.objects.filter(bot=bot_config).acount()
    assert remaining == 1
    leftover = await MessageMapping.objects.aget(bot=bot_config, owner_message_id=77)
    assert leftover.user_message_id == 11
