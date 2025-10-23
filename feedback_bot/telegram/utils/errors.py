import contextlib
import html
import json
import logging
import traceback

from django.conf import settings
from telegram import Update
from telegram.constants import MessageLimit
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


def _build_messages(parts: list[str]) -> list[str]:
    messages: list[str] = []
    limit = MessageLimit.MAX_TEXT_LENGTH
    for part in parts:
        chunk = part
        while chunk:
            current = chunk[:limit]
            chunk = chunk[limit:]
            if messages:
                last = messages[-1]
                if len(last) + 1 + len(current) <= limit:
                    messages[-1] = f'{last}\n{current}'
                    continue
            messages.append(current)
    return messages


async def report_error(update: Update | None, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error('Exception while handling an update', exc_info=context.error)
    chat_id = settings.TELEGRAM_ADMIN_CHAT_ID
    if not chat_id:
        return

    error = context.error
    message_parts = ['Exception raised while handling an update']
    if error is not None:
        message_parts.append('error:')
        message_parts.append(f'<code>{html.escape(repr(error))}</code>')

    if update:
        try:
            payload = json.dumps(update.to_dict(), ensure_ascii=False, indent=2)
        except AttributeError:
            payload = repr(update)
        message_parts.append(f'<pre>{html.escape(payload)}</pre>')

    if error is not None:
        traceback_text = ''.join(
            traceback.format_exception(None, error, getattr(error, '__traceback__', None))
        )
        message_parts.append(f'<pre>{html.escape(traceback_text)}</pre>')

    base_kwargs = {'chat_id': chat_id, 'parse_mode': 'HTML'}
    topic_id = getattr(settings, 'TELEGRAM_LOG_TOPIC_ID', None)
    if topic_id:
        with contextlib.suppress(TypeError, ValueError):
            base_kwargs['message_thread_id'] = int(topic_id)

    for text in _build_messages(message_parts):
        await context.bot.send_message(**base_kwargs, text=text)
