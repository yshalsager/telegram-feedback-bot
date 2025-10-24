"""Helpers shared across broadcast handlers."""

import logging
from asyncio import sleep
from collections.abc import Awaitable, Callable, Iterable
from datetime import UTC, date, datetime, timedelta
from typing import Any

from django.utils.translation import gettext_lazy as _
from telegram import Message
from telegram.constants import MessageEntityType
from telegram.error import RetryAfter, TelegramError
from telegram.ext import ExtBot

logger = logging.getLogger(__name__)

SLEEP_AFTER_SEND = 0.035

RecordCallback = Callable[[int, int], Awaitable[None]] | None


async def broadcast_to_chats(
    bot: ExtBot, message: Message, chat_ids: Iterable[int], record: RecordCallback = None
) -> tuple[int, int]:
    sent = 0
    failed = 0
    for chat_id in chat_ids:
        try:
            copied = await bot.copy_message(
                chat_id=chat_id,
                from_chat_id=message.chat_id,
                message_id=message.message_id,
            )
        except RetryAfter as err:
            await sleep(err.retry_after + 1)
            try:
                copied = await bot.copy_message(
                    chat_id=chat_id,
                    from_chat_id=message.chat_id,
                    message_id=message.message_id,
                )
            except TelegramError as retry_err:
                failed += 1
                logger.warning('Failed to broadcast to %s after retry: %s', chat_id, retry_err)
                continue
        except TelegramError as err:
            failed += 1
            logger.warning('Failed to broadcast to %s: %s', chat_id, err)
            continue

        sent += 1
        if record is not None:
            await record(chat_id, copied.message_id)
        await sleep(SLEEP_AFTER_SEND)
    return sent, failed


def parse_broadcast_filters(raw: str) -> tuple[dict[str, Any], str | None]:  # noqa: C901, PLR0911, PLR0912
    text = (raw or '').strip()
    if not text or text.lower() == 'done':
        return {}, None

    filters: dict[str, Any] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split()
        keyword = parts[0].lower()

        if keyword == 'joined_after' and len(parts) >= 2:
            parsed = _parse_datetime(parts[1])
            if parsed is None:
                return {}, 'Invalid date for "joined_after". Use YYYY-MM-DD.'
            filters['joined_after'] = parsed
            continue

        if keyword == 'joined_before' and len(parts) >= 2:
            parsed = _parse_datetime(parts[1])
            if parsed is None:
                return {}, 'Invalid date for "joined_before". Use YYYY-MM-DD.'
            filters['joined_before'] = parsed
            continue

        if keyword == 'active_within' and len(parts) >= 2:
            try:
                days = int(parts[1])
            except ValueError:
                return {}, 'Invalid number for "active_within".'
            if days < 0:
                return {}, '"active_within" must be positive.'
            filters['active_after'] = datetime.now(UTC) - timedelta(days=days)
            continue

        if keyword == 'username_only':
            allow = True
            if len(parts) >= 2:
                allow = parts[1].lower() in {'yes', 'true', '1'}
            filters['username_only'] = allow
            continue

        if keyword == 'sample_every' and len(parts) >= 2:
            try:
                stride = int(parts[1])
            except ValueError:
                return {}, 'Invalid number for "sample_every".'
            if stride < 1:
                return {}, '"sample_every" must be at least 1.'
            filters['sample_stride'] = stride
            continue

        return {}, f'Unrecognized filter: "{line}".'

    return filters, None


def filters_help_text() -> str:
    return str(
        _(
            'Reply with filters (one per line) or "done" to send to everyone:\n'
            '- joined_after YYYY-MM-DD\n'
            '- joined_before YYYY-MM-DD\n'
            '- active_within DAYS\n'
            '- username_only [yes|no]\n'
            '- sample_every N'
        )
    )


def extract_filters_text(message: Message) -> str:
    if not message or not message.text:
        return ''

    text = message.text
    if not message.entities:
        return text.replace('/broadcast', '', 1).strip()

    for entity in message.entities:
        if entity.type != MessageEntityType.BOT_COMMAND or entity.offset != 0:
            continue
        end = entity.length
        return text[end:].strip()

    return text.strip()


def _parse_datetime(raw: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        try:
            parsed_date = date.fromisoformat(raw)
        except ValueError:
            return None
        parsed = datetime.combine(parsed_date, datetime.min.time(), tzinfo=UTC)
    else:
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
    return parsed
