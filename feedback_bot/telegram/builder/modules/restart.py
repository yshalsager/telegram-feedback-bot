"""Bot restart module"""

from os import execlp

import orjson
from django.conf import settings
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from feedback_bot.telegram.builder.filters import is_admin


async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Restart the bot."""
    restart_message = await update.message.reply_text(
        'Restarting, please wait...',
        reply_to_message_id=update.message.message_id,
    )
    chat_info = {'chat': restart_message.chat_id, 'message': restart_message.message_id}
    (settings.BASE_DIR / 'restart.json').write_bytes(orjson.dumps(chat_info))
    execlp('uv', 'uv', 'run', 'granian', '--interface', 'asgi', 'config.asgi:application')  # noqa: S606, S607


HANDLERS = [CommandHandler('restart', restart, is_admin)]
