"""Tests for feedback message handlers."""

from __future__ import annotations

import datetime as dt
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from feedback_bot.models import BannedUser, Bot, BotStats, FeedbackChat, MessageMapping
from feedback_bot.telegram.feedback_bot.modules import messages as messages_module
from tests.feedback_bot.telegram.factories import build_message

from telegram import MessageId

pytestmark = [pytest.mark.asyncio, pytest.mark.django_db]


def _build_context(bot_config, *, bot_id: int, send_message=None, edit_message_text=None):
    bot = SimpleNamespace(
        id=bot_id,
        send_message=send_message or AsyncMock(),
        edit_message_text=edit_message_text or AsyncMock(),
        create_forum_topic=AsyncMock(return_value=SimpleNamespace(message_thread_id=999_999)),
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
    await FeedbackChat.objects.filter(bot=bot_config).adelete()
    await MessageMapping.objects.filter(bot=bot_config).adelete()

    user_message = build_message(999, message_id=11, text='hi there')

    forwarded = SimpleNamespace(message_id=42, link=None)
    forward_mock = AsyncMock(return_value=forwarded)
    reply_mock = AsyncMock()
    _patch_message_method(monkeypatch, 'forward', forward_mock)
    _patch_message_method(monkeypatch, 'reply_text', reply_mock)

    send_mock = AsyncMock()
    context = _build_context(bot_config, bot_id=bot_config.telegram_id, send_message=send_mock)
    update = SimpleNamespace(effective_message=user_message)

    await messages_module.forward_feedback(update, context)

    chat = await FeedbackChat.objects.aget(bot=bot_config, user_telegram_id=999)
    assert chat.topic_id is None
    assert chat.last_feedback_at is not None
    assert abs((chat.last_feedback_at - user_message.date).total_seconds()) < 1

    mapping = await MessageMapping.objects.aget(bot=bot_config, user_message_id=11)
    assert mapping.owner_message_id == 42

    stats = await BotStats.objects.aget(bot=bot_config)
    assert stats.incoming_messages == 1

    forward_mock.assert_awaited_once()
    reply_mock.assert_awaited_once_with(user_message, 'Thanks', reply_to_message_id=11)
    send_mock.assert_awaited_once()
    intro_payload = send_mock.await_args.kwargs
    assert intro_payload['chat_id'] == bot_config.owner_id
    assert intro_payload['parse_mode'] == 'HTML'
    assert intro_payload['disable_web_page_preview'] is True
    assert intro_payload['text'].startswith('Tester')


async def test_forward_feedback_private_mode_uses_copy(monkeypatch, feedback_app):
    _, bot_config = feedback_app
    await FeedbackChat.objects.filter(bot=bot_config).adelete()
    await MessageMapping.objects.filter(bot=bot_config).adelete()
    await Bot.objects.filter(pk=bot_config.pk).aupdate(
        communication_mode=Bot.CommunicationMode.PRIVATE
    )
    bot_config.communication_mode = Bot.CommunicationMode.PRIVATE

    user_message = build_message(999, message_id=11, text='hi there', username='tester')

    copied = SimpleNamespace(message_id=55)
    copy_mock = AsyncMock(return_value=copied)
    forward_mock = AsyncMock()
    reply_mock = AsyncMock()
    _patch_message_method(monkeypatch, 'copy', copy_mock)
    _patch_message_method(monkeypatch, 'forward', forward_mock)
    _patch_message_method(monkeypatch, 'reply_text', reply_mock)

    send_mock = AsyncMock()
    context = _build_context(bot_config, bot_id=bot_config.telegram_id, send_message=send_mock)
    update = SimpleNamespace(effective_message=user_message)

    await messages_module.forward_feedback(update, context)

    copy_mock.assert_awaited_once()
    forward_mock.assert_not_awaited()
    kwargs = copy_mock.await_args.kwargs
    assert kwargs['chat_id'] == bot_config.owner_id
    assert 'message_thread_id' not in kwargs

    intro_payload = send_mock.await_args.kwargs
    assert '@' not in intro_payload['text']
    assert 'tg://user' not in intro_payload['text']
    reply_mock.assert_awaited_once_with(user_message, 'Thanks', reply_to_message_id=11)


async def test_forward_feedback_anonymous_topic(monkeypatch, feedback_app):
    _, bot_config = feedback_app
    await FeedbackChat.objects.filter(bot=bot_config).adelete()
    await MessageMapping.objects.filter(bot=bot_config).adelete()
    await Bot.objects.filter(pk=bot_config.pk).aupdate(
        communication_mode=Bot.CommunicationMode.ANONYMOUS,
        forward_chat_id=-100222333,
    )
    bot_config.communication_mode = Bot.CommunicationMode.ANONYMOUS
    bot_config.forward_chat_id = -100222333

    user_message = build_message(999, message_id=11, text='hi there', username='tester')

    copied = SimpleNamespace(message_id=60)
    copy_mock = AsyncMock(return_value=copied)
    forward_mock = AsyncMock()
    reply_mock = AsyncMock()
    _patch_message_method(monkeypatch, 'copy', copy_mock)
    _patch_message_method(monkeypatch, 'forward', forward_mock)
    _patch_message_method(monkeypatch, 'reply_text', reply_mock)

    send_mock = AsyncMock()
    context = _build_context(bot_config, bot_id=bot_config.telegram_id, send_message=send_mock)
    topic_mock = AsyncMock(return_value=SimpleNamespace(message_thread_id=444))
    context.bot.create_forum_topic = topic_mock

    update = SimpleNamespace(effective_message=user_message)

    await messages_module.forward_feedback(update, context)

    copy_mock.assert_awaited_once()
    forward_mock.assert_not_awaited()
    kwargs = copy_mock.await_args.kwargs
    assert kwargs['chat_id'] == bot_config.forward_chat_id
    assert kwargs['message_thread_id'] == 444

    topic_kwargs = topic_mock.await_args.kwargs
    assert topic_kwargs['name'].startswith('#')

    intro_payload = send_mock.await_args.kwargs
    assert intro_payload['message_thread_id'] == 444
    assert intro_payload['text'].startswith('#')
    assert 'tg://user' not in intro_payload['text']

    chat = await FeedbackChat.objects.aget(bot=bot_config, user_telegram_id=999)
    assert chat.topic_id == 444


async def test_forward_feedback_blocks_banned_user(monkeypatch, feedback_app):
    _, bot_config = feedback_app
    await FeedbackChat.objects.filter(bot=bot_config).adelete()
    await MessageMapping.objects.filter(bot=bot_config).adelete()
    await BannedUser.objects.aget_or_create(bot=bot_config, user_telegram_id=999)

    user_message = build_message(999, message_id=11, text='hi there')

    forward_mock = AsyncMock()
    reply_mock = AsyncMock()
    _patch_message_method(monkeypatch, 'forward', forward_mock)
    _patch_message_method(monkeypatch, 'reply_text', reply_mock)

    context = _build_context(bot_config, bot_id=bot_config.telegram_id)
    update = SimpleNamespace(effective_message=user_message)

    await messages_module.forward_feedback(update, context)

    assert forward_mock.await_count == 0
    reply_mock.assert_not_awaited()


async def test_forward_feedback_throttles_when_antiflood_enabled(monkeypatch, feedback_app):
    _, bot_config = feedback_app
    await Bot.objects.filter(pk=bot_config.pk).aupdate(
        antiflood_enabled=True, antiflood_seconds=120
    )
    await bot_config.arefresh_from_db()
    await FeedbackChat.objects.filter(bot=bot_config).adelete()
    await MessageMapping.objects.filter(bot=bot_config).adelete()

    first_timestamp = dt.datetime(2025, 1, 1, 12, 0, tzinfo=dt.UTC)
    first_message = build_message(999, message_id=11, text='hello', date=first_timestamp)
    forwarded = SimpleNamespace(message_id=42, link=None)
    forward_mock = AsyncMock(return_value=forwarded)
    reply_mock = AsyncMock()
    _patch_message_method(monkeypatch, 'forward', forward_mock)
    _patch_message_method(monkeypatch, 'reply_text', reply_mock)

    context = _build_context(bot_config, bot_id=bot_config.telegram_id)
    update = SimpleNamespace(effective_message=first_message)

    await messages_module.forward_feedback(update, context)

    assert forward_mock.await_count == 1
    assert reply_mock.await_count == 1
    assert reply_mock.await_args_list[0].args[1] == 'Thanks'

    second_message = build_message(
        999,
        message_id=12,
        text='again',
        date=first_timestamp + dt.timedelta(seconds=30),
    )
    throttled_update = SimpleNamespace(effective_message=second_message)

    await messages_module.forward_feedback(throttled_update, context)

    assert forward_mock.await_count == 1
    assert reply_mock.await_count == 2
    throttled_call = reply_mock.await_args_list[-1]
    assert throttled_call.args[0] is second_message
    assert (
        throttled_call.args[1] == 'Too many messages. Please wait 120 seconds before sending again.'
    )
    assert throttled_call.kwargs == {'reply_to_message_id': 12}

    chat_after_warning = await FeedbackChat.objects.aget(bot=bot_config, user_telegram_id=999)
    assert chat_after_warning.last_warning_at is not None

    third_message = build_message(
        999,
        message_id=13,
        text='still again',
        date=first_timestamp + dt.timedelta(seconds=40),
    )
    third_update = SimpleNamespace(effective_message=third_message)

    await messages_module.forward_feedback(third_update, context)

    assert forward_mock.await_count == 1
    assert reply_mock.await_count == 2

    fourth_message = build_message(
        999,
        message_id=14,
        text='after wait',
        date=first_timestamp + dt.timedelta(seconds=130),
    )
    fourth_update = SimpleNamespace(effective_message=fourth_message)

    await messages_module.forward_feedback(fourth_update, context)

    assert forward_mock.await_count == 2
    assert reply_mock.await_count == 3
    assert reply_mock.await_args_list[-1].args[1] == 'Thanks'

    chat_after_reset = await FeedbackChat.objects.aget(bot=bot_config, user_telegram_id=999)
    assert chat_after_reset.last_warning_at is None


async def test_forward_feedback_blocks_disallowed_media(monkeypatch, feedback_app):
    _, bot_config = feedback_app
    await FeedbackChat.objects.filter(bot=bot_config).adelete()
    await MessageMapping.objects.filter(bot=bot_config).adelete()
    await Bot.objects.filter(pk=bot_config.pk).aupdate(allow_photo_messages=False)
    await bot_config.arefresh_from_db()

    user_message = build_message(999, message_id=11, text='')
    user_message._frozen = False
    user_message.photo = [SimpleNamespace(file_id='ph-1')]
    user_message._frozen = True

    forward_mock = AsyncMock()
    reply_mock = AsyncMock()
    _patch_message_method(monkeypatch, 'forward', forward_mock)
    _patch_message_method(monkeypatch, 'reply_text', reply_mock)

    context = _build_context(bot_config, bot_id=bot_config.telegram_id)
    update = SimpleNamespace(effective_message=user_message)

    await messages_module.forward_feedback(update, context)

    assert forward_mock.await_count == 0
    reply_mock.assert_awaited_once_with(
        user_message, 'This bot does not accept photos.', reply_to_message_id=11
    )
    assert not await FeedbackChat.objects.filter(bot=bot_config).aexists()


async def test_edit_forwarded_feedback_updates_owner_message(monkeypatch, feedback_app):
    _, bot_config = feedback_app
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


async def test_edit_forwarded_feedback_blocks_disallowed_media(monkeypatch, feedback_app):
    _, bot_config = feedback_app
    await FeedbackChat.objects.filter(bot=bot_config).adelete()
    await MessageMapping.objects.filter(bot=bot_config).adelete()
    await Bot.objects.filter(pk=bot_config.pk).aupdate(allow_video_messages=False)
    await bot_config.arefresh_from_db()

    feedback_chat, _ = await FeedbackChat.objects.aget_or_create(
        bot=bot_config,
        user_telegram_id=999,
        defaults={'username': ''},
    )

    await MessageMapping.objects.aupdate_or_create(
        bot=bot_config,
        user_message_id=11,
        defaults={'user_chat': feedback_chat, 'owner_message_id': 22},
    )

    edited_payload = build_message(999, message_id=11, text='')
    edited_payload._frozen = False
    edited_payload.video = SimpleNamespace(file_id='vid-1')
    edited_payload._frozen = True

    forward_mock = AsyncMock()
    reply_mock = AsyncMock()
    _patch_message_method(monkeypatch, 'forward', forward_mock)
    _patch_message_method(monkeypatch, 'reply_text', reply_mock)

    context = _build_context(bot_config, bot_id=bot_config.telegram_id)
    update = SimpleNamespace(effective_message=edited_payload)

    await messages_module.edit_forwarded_feedback(update, context)

    assert forward_mock.await_count == 0
    reply_mock.assert_awaited_once_with(
        edited_payload, 'This bot does not accept videos.', reply_to_message_id=11
    )
    mapping = await MessageMapping.objects.aget(bot=bot_config, user_message_id=11)
    assert mapping.owner_message_id == 22


async def test_reply_to_feedback_without_reply_in_private_topic(monkeypatch, feedback_app):
    _, bot_config = feedback_app
    await FeedbackChat.objects.filter(bot=bot_config).adelete()
    await MessageMapping.objects.filter(bot=bot_config).adelete()
    await Bot.objects.filter(pk=bot_config.pk).aupdate(
        communication_mode=Bot.CommunicationMode.PRIVATE,
        forward_chat_id=-100222333,
    )
    bot_config.communication_mode = Bot.CommunicationMode.PRIVATE
    bot_config.forward_chat_id = -100222333

    feedback_chat, _ = await FeedbackChat.objects.aget_or_create(
        bot=bot_config,
        user_telegram_id=999,
        defaults={'username': '', 'topic_id': 777},
    )
    feedback_chat.topic_id = 777
    await feedback_chat.asave(update_fields=['topic_id'])

    owner_reply = build_message(
        bot_config.owner_id,
        message_id=31,
        text='answer',
        chat_id=-100222333,
        chat_type='supergroup',
    )
    owner_reply._frozen = False
    owner_reply.message_thread_id = 777
    owner_reply._frozen = True

    copy_mock = AsyncMock(return_value=MessageId(88))
    reaction_mock = AsyncMock()
    _patch_message_method(monkeypatch, 'copy', copy_mock)
    _patch_message_method(monkeypatch, 'set_reaction', reaction_mock)

    context = _build_context(bot_config, bot_id=bot_config.telegram_id)
    update = SimpleNamespace(effective_message=owner_reply)

    await messages_module.reply_to_feedback(update, context)

    copy_mock.assert_awaited_once_with(
        owner_reply,
        chat_id=999,
        reply_to_message_id=None,
        allow_sending_without_reply=True,
    )
    reaction_mock.assert_awaited_once_with(owner_reply, '👍')

    mapping = await MessageMapping.objects.select_related('user_chat').aget(
        bot=bot_config, owner_message_id=31
    )
    assert mapping.user_chat == feedback_chat
    assert mapping.user_message_id == 88


async def test_reply_to_feedback_copies_message(monkeypatch, feedback_app):
    _, bot_config = feedback_app
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
        forward_origin=SimpleNamespace(),
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


async def test_reply_to_feedback_allows_forward_origin_in_private(monkeypatch, feedback_app):
    app, bot_config = feedback_app
    bot_config.forward_chat_id = None

    await FeedbackChat.objects.filter(bot=bot_config).adelete()
    await MessageMapping.objects.filter(bot=bot_config).adelete()

    forwarded_holder: dict[str, object] = {}

    async def fake_forward(self, chat_id, message_thread_id=None, **kwargs):  # type: ignore[override]
        forwarded = build_message(
            bot_config.telegram_id,
            message_id=222,
            text=self.text,
            chat_id=chat_id,
            chat_type='private',
            is_bot=True,
            forward_origin=SimpleNamespace(),
        )
        forwarded.set_bot(app.bot)
        forwarded_holder['message'] = forwarded
        return forwarded

    monkeypatch.setattr('telegram._message.Message.forward', fake_forward)
    monkeypatch.setattr('telegram._message.Message.reply_text', AsyncMock())

    context = _build_context(bot_config, bot_id=bot_config.telegram_id)

    user_message = build_message(999, message_id=11, text='hello')
    await messages_module.forward_feedback(SimpleNamespace(effective_message=user_message), context)

    assert 'message' in forwarded_holder

    copy_mock = AsyncMock(return_value=MessageId(66))
    reaction_mock = AsyncMock()
    _patch_message_method(monkeypatch, 'copy', copy_mock)
    _patch_message_method(monkeypatch, 'set_reaction', reaction_mock)

    reply_target = forwarded_holder['message']
    owner_reply = build_message(
        bot_config.owner_id,
        message_id=31,
        text='response',
        chat_id=bot_config.owner_id,
        chat_type='private',
        reply_to=reply_target,
    )

    await messages_module.reply_to_feedback(SimpleNamespace(effective_message=owner_reply), context)

    copy_mock.assert_awaited_once_with(
        owner_reply,
        chat_id=999,
        reply_to_message_id=11,
        allow_sending_without_reply=True,
    )
    reaction_mock.assert_awaited_once_with(owner_reply, '👍')


async def test_edit_forwarded_feedback_notifies_without_link(monkeypatch, feedback_app):
    _, bot_config = feedback_app
    bot_config.forward_chat_id = None

    await FeedbackChat.objects.filter(bot=bot_config).adelete()
    await MessageMapping.objects.filter(bot=bot_config).adelete()

    send_mock = AsyncMock()
    context = _build_context(bot_config, bot_id=bot_config.telegram_id, send_message=send_mock)

    forwards: list = []

    async def fake_forward(self, chat_id, message_thread_id=None, **kwargs):  # type: ignore[override]
        forwarded = build_message(
            bot_config.telegram_id,
            message_id=200 + len(forwards),
            text=self.text,
            chat_id=chat_id,
            chat_type='private',
            is_bot=True,
        )
        forwarded.set_bot(context.bot)
        forwards.append(forwarded)
        return forwarded

    monkeypatch.setattr('telegram._message.Message.forward', fake_forward)
    monkeypatch.setattr('telegram._message.Message.reply_text', AsyncMock())

    user_message = build_message(999, message_id=11, text='hello')
    await messages_module.forward_feedback(SimpleNamespace(effective_message=user_message), context)

    assert send_mock.await_count == 1

    edit_message = build_message(999, message_id=11, text='updated hello')
    await messages_module.edit_forwarded_feedback(
        SimpleNamespace(effective_message=edit_message), context
    )

    assert send_mock.await_count == 2
    edit_payload = send_mock.await_args_list[-1].kwargs
    assert edit_payload['chat_id'] == bot_config.owner_id
    assert edit_payload['text'] == 'User updated their message.'
