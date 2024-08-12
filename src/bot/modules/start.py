from html import escape

from plate import Plate
from pyrogram import Client, filters
from pyrogram.types import Message

from src.bot.utils.analytics import add_new_chat_to_db
from src.builder.db.crud import get_bot, update_bot_group
from src.builder.db.models.bot import Bot
from src.common.utils.i18n import localize
from src.common.utils.telegram_handlers import tg_exceptions_handler


@Client.on_message(filters.command('start'))
@Client.on_message(filters.command('help'))
@add_new_chat_to_db
@tg_exceptions_handler
@localize
async def start(client: Client, message: Message, i18n: Plate) -> None:
    bot: Bot | None = get_bot(client.me.id)
    if not bot:
        return
    await message.reply_text(
        escape(bot.bot_settings.start_message or i18n('default_start', name=bot.name)),
        reply_to_message_id=message.reply_to_message_id,
    )


@Client.on_message(filters.group & filters.new_chat_members)
@tg_exceptions_handler
@localize
async def added_to_group(client: Client, update: Message, i18n: Plate) -> None:
    if not next((member for member in update.new_chat_members if member.id == client.me.id), None):
        return
    update_bot_group(client.me.id, update.chat.id)
    bot: Bot | None = get_bot(client.me.id)
    assert bot is not None
    await update.reply_text(i18n('added_to_group', name=bot.name, chat=update.chat.full_name))
