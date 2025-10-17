"""Helpers shared across broadcast handlers."""

import logging
from asyncio import sleep
from collections.abc import Awaitable, Callable, Iterable

from telegram import Message
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
