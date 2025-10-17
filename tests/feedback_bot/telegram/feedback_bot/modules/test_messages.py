"""Tests for feedback message handlers."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from feedback_bot.models import BotStats, FeedbackChat, MessageMapping
from feedback_bot.telegram.feedback_bot.modules import messages as messages_module
from tests.feedback_bot.telegram.factories import build_message

from telegram import MessageId

pytestmark = [pytest.mark.asyncio, pytest.mark.django_db]


def _build_context(bot_config, *, bot_id: int, send_message=None, edit_message_text=None):
    bot = SimpleNamespace(
        id=bot_id,
        send_message=send_message or AsyncMock(),
        edit_message_text=edit_message_text or AsyncMock(),
    )
    bot_data = {'bot_config': bot_config}
    application = SimpleNamespace(bot_data=bot_data, bot=bot)
    return SimpleNamespace(application=application, bot=bot, bot_data=bot_data)


def _patch_message_method(monkeypatch, method: str, mock: AsyncMock) -> None:
    async def wrapper(self, *args, **kwargs):
        return await mock(self, *args, **kwargs)

    monkeypatch.setattr(f'telegram._message.Message.{method}', wrapper)


async def test_forward_feedback_creates_mapping(monkeypatch, feedback_app):
    _, bot_config = feedback_app
    bot_config.confirmations_on = True
    await FeedbackChat.objects.filter(bot=bot_config).adelete()
    await MessageMapping.objects.filter(bot=bot_config).adelete()

    user_message = build_message(999, message_id=11, text='hi there')

    forwarded = SimpleNamespace(message_id=42, link=None)
    forward_mock = AsyncMock(return_value=forwarded)
    reply_mock = AsyncMock()
    _patch_message_method(monkeypatch, 'forward', forward_mock)
    _patch_message_method(monkeypatch, 'reply_text', reply_mock)

    context = _build_context(bot_config, bot_id=bot_config.telegram_id)
    update = SimpleNamespace(effective_message=user_message)

    await messages_module.forward_feedback(update, context)

    chat = await FeedbackChat.objects.aget(bot=bot_config, user_telegram_id=999)
    assert chat.topic_id is None

    mapping = await MessageMapping.objects.aget(bot=bot_config, user_message_id=11)
    assert mapping.owner_message_id == 42

    stats = await BotStats.objects.aget(bot=bot_config)
    assert stats.incoming_messages == 1

    forward_mock.assert_awaited_once()
    reply_mock.assert_awaited_once_with(user_message, 'Thanks', reply_to_message_id=11)


async def test_edit_forwarded_feedback_updates_owner_message(monkeypatch, feedback_app):
    _, bot_config = feedback_app
    bot_config.confirmations_on = True
    await FeedbackChat.objects.filter(bot=bot_config).adelete()
    await MessageMapping.objects.filter(bot=bot_config).adelete()
    bot_config.forward_chat_id = -100222333

    feedback_chat, _ = await FeedbackChat.objects.aget_or_create(
        bot=bot_config,
        user_telegram_id=999,
        defaults={'username': '', 'topic_id': 555},
    )
    feedback_chat.topic_id = 555
    await feedback_chat.asave(update_fields=['topic_id'])
    await MessageMapping.objects.aupdate_or_create(
        bot=bot_config,
        user_message_id=11,
        defaults={'user_chat': feedback_chat, 'owner_message_id': 22},
    )

    edited_payload = build_message(999, message_id=11, text='updated text')
    update = SimpleNamespace(effective_message=edited_payload)

    forwarded = SimpleNamespace(message_id=44, link='https://t.me/c/222333/44?thread=555')
    forward_mock = AsyncMock(return_value=forwarded)
    _patch_message_method(monkeypatch, 'forward', forward_mock)

    send_mock = AsyncMock()
    context = _build_context(
        bot_config,
        bot_id=bot_config.telegram_id,
        send_message=send_mock,
    )

    await messages_module.edit_forwarded_feedback(update, context)

    mapping = await MessageMapping.objects.aget(bot=bot_config, user_message_id=11)
    assert mapping.owner_message_id == 44
    send_mock.assert_awaited_once()
    payload = send_mock.await_args.kwargs
    assert payload['chat_id'] == -100222333
    assert payload['message_thread_id'] == 555
    assert forwarded.link in payload['text']


async def test_reply_to_feedback_copies_message(monkeypatch, feedback_app):
    _, bot_config = feedback_app
    bot_config.confirmations_on = True
    await FeedbackChat.objects.filter(bot=bot_config).adelete()
    await MessageMapping.objects.filter(bot=bot_config).adelete()

    feedback_chat, _ = await FeedbackChat.objects.aget_or_create(
        bot=bot_config,
        user_telegram_id=999,
        defaults={'username': '', 'topic_id': 555},
    )
    feedback_chat.topic_id = 555
    await feedback_chat.asave(update_fields=['topic_id'])
    await MessageMapping.objects.aupdate_or_create(
        bot=bot_config,
        user_message_id=11,
        defaults={'user_chat': feedback_chat, 'owner_message_id': 22},
    )

    reply_target = build_message(
        bot_config.telegram_id,
        message_id=22,
        chat_id=-100222333,
        chat_type='supergroup',
        is_bot=True,
    )

    owner_reply = build_message(
        bot_config.owner_id,
        message_id=31,
        text='answer',
        chat_id=-100222333,
        chat_type='supergroup',
        reply_to=reply_target,
    )

    copy_mock = AsyncMock(return_value=MessageId(66))
    reaction_mock = AsyncMock()
    _patch_message_method(monkeypatch, 'copy', copy_mock)
    _patch_message_method(monkeypatch, 'set_reaction', reaction_mock)

    context = _build_context(bot_config, bot_id=bot_config.telegram_id)
    update = SimpleNamespace(effective_message=owner_reply)

    await messages_module.reply_to_feedback(update, context)

    mapping = await MessageMapping.objects.aget(bot=bot_config, user_message_id=66)
    assert mapping.owner_message_id == 31

    stats = await BotStats.objects.aget(bot=bot_config)
    assert stats.outgoing_messages == 1

    copy_mock.assert_awaited_once_with(
        owner_reply,
        chat_id=999,
        reply_to_message_id=11,
        allow_sending_without_reply=True,
    )
    reaction_mock.assert_awaited_once_with(owner_reply, '👍')


async def test_edit_reply_to_feedback_updates_user_message(monkeypatch, feedback_app):
    _, bot_config = feedback_app
    bot_config.confirmations_on = True
    await FeedbackChat.objects.filter(bot=bot_config).adelete()
    await MessageMapping.objects.filter(bot=bot_config).adelete()

    feedback_chat, _ = await FeedbackChat.objects.aget_or_create(
        bot=bot_config,
        user_telegram_id=999,
        defaults={'username': ''},
    )
    await MessageMapping.objects.aupdate_or_create(
        bot=bot_config,
        user_message_id=66,
        defaults={'user_chat': feedback_chat, 'owner_message_id': 31},
    )

    reply_target = build_message(
        bot_config.telegram_id,
        message_id=22,
        chat_id=bot_config.owner_id,
        is_bot=True,
    )

    edited_owner = build_message(
        bot_config.owner_id,
        message_id=31,
        text='updated answer',
        chat_id=bot_config.owner_id,
        reply_to=reply_target,
    )

    reply_mock = AsyncMock()
    _patch_message_method(monkeypatch, 'reply_text', reply_mock)

    edit_mock = AsyncMock()
    context = _build_context(
        bot_config,
        bot_id=bot_config.telegram_id,
        edit_message_text=edit_mock,
    )
    update = SimpleNamespace(effective_message=edited_owner)

    await messages_module.edit_reply_to_feedback(update, context)

    edit_mock.assert_awaited_once_with(
        chat_id=999,
        message_id=66,
        text=edited_owner.text_html,
        parse_mode='HTML',
    )
    reply_mock.assert_awaited_once_with(
        edited_owner, 'Sent message updated', reply_to_message_id=31
    )
