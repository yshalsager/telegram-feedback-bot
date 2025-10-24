"""Feedback message forwarding and reply handlers."""

from __future__ import annotations

from datetime import UTC, datetime
from html import escape

from django.utils.translation import gettext as _
from telegram import (
    InputMediaAudio,
    InputMediaDocument,
    InputMediaPhoto,
    InputMediaVideo,
    Message,
    Update,
)
from telegram.constants import ChatType, ParseMode
from telegram.error import BadRequest
from telegram.ext import ContextTypes, MessageHandler, filters

from feedback_bot.crud import (
    bump_incoming_messages,
    bump_outgoing_messages,
    clear_feedback_chat_mappings,
    ensure_feedback_chat,
    get_owner_message_mapping,
    get_user_message_mapping,
    is_user_banned,
    save_incoming_mapping,
    save_outgoing_mapping,
    set_feedback_chat_topic,
    update_incoming_mapping,
)
from feedback_bot.models import Bot, FeedbackChat, MessageMapping


async def _create_topic(
    context: ContextTypes.DEFAULT_TYPE,
    bot_config: Bot,
    message: Message,
    feedback_chat: FeedbackChat,
) -> int | None:
    if not bot_config.forward_chat_id:
        return None

    name = (
        message.chat.full_name
        or message.chat.title
        or message.chat.username
        or f'{message.from_user.first_name}'
    )
    topic = await context.bot.create_forum_topic(chat_id=bot_config.forward_chat_id, name=name[:64])

    intro_lines = [escape(name)]
    if message.from_user.username:
        intro_lines.append(f'@{escape(message.from_user.username)}')
    intro_lines.append(f'<a href="tg://user?id={message.from_user.id}">{message.from_user.id}</a>')
    await context.bot.send_message(
        chat_id=bot_config.forward_chat_id,
        message_thread_id=topic.message_thread_id,
        text='\n'.join(intro_lines),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )

    await set_feedback_chat_topic(feedback_chat, topic.message_thread_id)
    return feedback_chat.topic_id


async def _ensure_topic(
    context: ContextTypes.DEFAULT_TYPE,
    bot_config: Bot,
    message: Message,
    feedback_chat: FeedbackChat,
) -> int | None:
    if not bot_config.forward_chat_id:
        return None

    if feedback_chat.topic_id:
        return feedback_chat.topic_id

    return await _create_topic(context, bot_config, message, feedback_chat)


async def _forward_with_topic_fallback(
    context: ContextTypes.DEFAULT_TYPE,
    bot_config: Bot,
    message: Message,
    feedback_chat: FeedbackChat,
    destination_chat_id: int,
    topic_id: int | None,
) -> tuple[Message, int | None]:
    try:
        forwarded = await message.forward(
            chat_id=destination_chat_id,
            message_thread_id=topic_id,
        )
        return forwarded, topic_id
    except BadRequest as exc:  # pragma: no cover - topic recreation path
        if not bot_config.forward_chat_id or not _is_topic_missing(exc):
            raise
        await clear_feedback_chat_mappings(bot_config, feedback_chat)
        await set_feedback_chat_topic(feedback_chat, None)
        new_topic = await _create_topic(context, bot_config, message, feedback_chat)
        forwarded = await message.forward(
            chat_id=destination_chat_id,
            message_thread_id=new_topic,
        )
        return forwarded, new_topic


def _is_topic_missing(error: BadRequest) -> bool:
    payload = error.message.lower()
    return 'thread' in payload and ('deleted' in payload or 'not found' in payload)


def _should_process_reply(bot_config: Bot, message: Message, bot_user_id: int) -> bool:
    is_private_chat = message.chat.type == ChatType.PRIVATE
    if is_private_chat and message.from_user.id != bot_config.owner_id:
        return False
    replied = message.reply_to_message
    if not replied:
        return False
    if (
        replied.forward_origin
        or getattr(replied, 'forward_from', None)
        or getattr(replied, 'forward_sender_name', None)
    ):
        return True
    return bool(replied.from_user and replied.from_user.id == bot_user_id)


async def _apply_edit(
    context: ContextTypes.DEFAULT_TYPE,
    mapping: MessageMapping,
    message: Message,
) -> bool:
    chat_id = mapping.user_chat.user_telegram_id
    target_message_id = mapping.user_message_id
    if not target_message_id:
        return False

    if message.text_html:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=target_message_id,
            text=message.text_html,
            parse_mode=ParseMode.HTML,
        )
        return True

    if message.caption_html:
        await context.bot.edit_message_caption(
            chat_id=chat_id,
            message_id=target_message_id,
            caption=message.caption_html,
            parse_mode=ParseMode.HTML,
        )
        return True

    media = _build_input_media(message)
    if not media:
        return False

    await context.bot.edit_message_media(
        chat_id=chat_id,
        message_id=target_message_id,
        media=media,
    )
    return True


def _build_input_media(message: Message):
    caption = message.caption or datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')

    if message.photo:
        return InputMediaPhoto(message.photo[-1].file_id, caption=caption)
    if message.video:
        return InputMediaVideo(message.video.file_id, caption=caption)
    if message.audio:
        return InputMediaAudio(message.audio.file_id, caption=caption)
    if message.voice:
        return InputMediaAudio(message.voice.file_id, caption=caption)
    if message.document:
        return InputMediaDocument(message.document.file_id, caption=caption)
    return None


MEDIA_BLOCK_RULES = (
    ('photo', 'allow_photo_messages', _('This bot does not accept photos.')),
    ('video', 'allow_video_messages', _('This bot does not accept videos.')),
    ('voice', 'allow_voice_messages', _('This bot does not accept voice messages.')),
    ('document', 'allow_document_messages', _('This bot does not accept documents.')),
    ('sticker', 'allow_sticker_messages', _('This bot does not accept stickers.')),
)


def _media_block_message(bot_config: Bot, message: Message) -> str | None:
    for attribute, flag, text in MEDIA_BLOCK_RULES:
        if getattr(message, attribute, None) and not getattr(bot_config, flag, True):
            return text
    return None


async def _send_intro_message(
    context: ContextTypes.DEFAULT_TYPE, destination_chat_id: int, message: Message
) -> None:
    intro_lines = [
        escape(
            message.chat.full_name
            or message.chat.title
            or message.chat.username
            or message.from_user.full_name
            or message.from_user.username
            or str(message.from_user.id)
        )
    ]
    if message.from_user.username:
        intro_lines.append(f'@{escape(message.from_user.username)}')
    intro_lines.append(f'<a href="tg://user?id={message.from_user.id}">{message.from_user.id}</a>')

    await context.bot.send_message(
        chat_id=destination_chat_id,
        text='\n'.join(intro_lines),
        parse_mode=ParseMode.HTML,
    )


async def forward_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if not message or not message.from_user:
        return

    bot_config: Bot = context.bot_data['bot_config']

    if await is_user_banned(bot_config.id, message.from_user.id):
        return

    destination_chat_id = bot_config.forward_chat_id or bot_config.owner_id
    if destination_chat_id is None:
        return

    if message.chat_id == destination_chat_id and message.from_user.id == bot_config.owner_id:
        return

    block_text = _media_block_message(bot_config, message)
    if block_text:
        await message.reply_text(block_text, reply_to_message_id=message.message_id)
        return

    feedback_chat, created = await ensure_feedback_chat(
        bot_config, message.from_user.id, message.from_user.username
    )
    if created and not bot_config.forward_chat_id:
        await _send_intro_message(context, destination_chat_id, message)
    topic_id = await _ensure_topic(context, bot_config, message, feedback_chat)

    forwarded, topic_id = await _forward_with_topic_fallback(
        context,
        bot_config,
        message,
        feedback_chat,
        destination_chat_id,
        topic_id,
    )

    await save_incoming_mapping(bot_config, feedback_chat, message.message_id, forwarded.message_id)
    await bump_incoming_messages(bot_config)

    text = bot_config.feedback_received_message or _('Thanks for your feedback!')
    await message.reply_text(text, reply_to_message_id=message.message_id)


async def edit_forwarded_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if not message or not message.from_user:
        return

    bot_config: Bot = context.bot_data['bot_config']

    if await is_user_banned(bot_config.id, message.from_user.id):
        return

    mapping = await get_user_message_mapping(bot_config, message.from_user.id, message.message_id)
    if mapping is None:
        return

    destination_chat_id = bot_config.forward_chat_id or bot_config.owner_id
    if destination_chat_id is None:
        return

    block_text = _media_block_message(bot_config, message)
    if block_text:
        await message.reply_text(block_text, reply_to_message_id=message.message_id)
        return

    feedback_chat = mapping.user_chat
    topic_id = feedback_chat.topic_id

    forwarded, topic_id = await _forward_with_topic_fallback(
        context,
        bot_config,
        message,
        feedback_chat,
        destination_chat_id,
        topic_id,
    )

    await update_incoming_mapping(bot_config, message.message_id, forwarded.message_id)

    message_kwargs: dict[str, object] = {
        'chat_id': destination_chat_id,
        'reply_to_message_id': forwarded.message_id,
    }
    if topic_id:
        message_kwargs['message_thread_id'] = topic_id

    if forwarded.link:
        message_kwargs['disable_web_page_preview'] = True
        text = _('User updated their message. New copy: {link}').format(link=forwarded.link)
    else:
        text = _('User updated their message.')

    await context.bot.send_message(text=text, **message_kwargs)


async def reply_to_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if not message or not message.from_user or not message.reply_to_message:
        return

    bot_config: Bot = context.bot_data['bot_config']
    if context.bot is None or context.bot.id is None:
        return

    if not _should_process_reply(bot_config, message, context.bot.id):
        return

    mapping = await get_owner_message_mapping(bot_config, message.reply_to_message.message_id)
    if mapping is None:
        return

    target_chat_id = mapping.user_chat.user_telegram_id
    reply_to = mapping.user_message_id if mapping.user_message_id else None

    result = await message.copy(
        chat_id=target_chat_id,
        reply_to_message_id=reply_to,
        allow_sending_without_reply=True,
    )

    await save_outgoing_mapping(
        bot_config, mapping.user_chat, result.message_id, message.message_id
    )
    await bump_outgoing_messages(bot_config)

    await message.set_reaction('👍')


async def edit_reply_to_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if not message or not message.reply_to_message:
        return

    bot_config: Bot = context.bot_data['bot_config']

    mapping = await get_owner_message_mapping(bot_config, message.message_id)
    if mapping is None:
        return

    edited = await _apply_edit(context, mapping, message)
    if edited:
        await message.reply_text(_('Sent message updated'), reply_to_message_id=message.id)


HANDLERS = [
    (
        MessageHandler(
            (filters.ChatType.PRIVATE | filters.ChatType.GROUPS) & filters.REPLY & ~filters.COMMAND,
            reply_to_feedback,
        ),
        -1,
    ),
    (
        MessageHandler(
            filters.UpdateType.EDITED_MESSAGE
            & (filters.ChatType.PRIVATE | filters.ChatType.GROUPS)
            & filters.REPLY
            & ~filters.COMMAND,
            edit_reply_to_feedback,
        ),
        -1,
    ),
    MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, forward_feedback),
    MessageHandler(
        filters.UpdateType.EDITED_MESSAGE & filters.ChatType.PRIVATE & ~filters.COMMAND,
        edit_forwarded_feedback,
    ),
]
