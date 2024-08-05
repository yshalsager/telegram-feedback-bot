"""Bot restart module"""

import json
from os import execl
from sys import executable

from pyrogram import Client, filters
from pyrogram.types import Message

from src import BOT_ADMINS, PARENT_DIR
from src.common.utils.filters import is_admin


@Client.on_message(filters.command('restart') & is_admin(BOT_ADMINS))
async def restart(_: Client, message: Message) -> None:
    """restarts the bot."""
    restart_message = await message.reply_text(
        'Restarting, please wait...',
        reply_to_message_id=message.reply_to_message_id,
    )
    chat_info = {'chat': restart_message.chat.id, 'message': restart_message.id}
    (PARENT_DIR / 'restart.json').write_text(json.dumps(chat_info))
    execl(executable, executable, '-m', __package__.split('.')[0])  # noqa: S606
