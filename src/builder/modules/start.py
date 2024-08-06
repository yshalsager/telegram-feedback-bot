from plate import Plate
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from src.builder.db.crud import add_user
from src.builder.utils.filters import is_whitelisted_user
from src.common.utils.i18n import localize
from src.common.utils.telegram_handlers import tg_exceptions_handler


@Client.on_message(filters.command('start') & filters.private & is_whitelisted_user())
@Client.on_callback_query(is_whitelisted_user() & filters.regex('^main$'))
@tg_exceptions_handler
@localize
async def start(_: Client, update: Message | CallbackQuery, i18n: Plate) -> None:
    message = i18n('welcome')
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(f"{i18n('add_bot')}", callback_data='add_bot')],
            [InlineKeyboardButton(f"{i18n('manage_bots')}", callback_data='manage_bots')],
            [InlineKeyboardButton(f"{i18n('manage_settings')}", callback_data='manage_settings')],
        ]
    )
    if isinstance(update, CallbackQuery):
        await update.edit_message_text(
            text=message,
            reply_markup=keyboard,
        )
        return
    await update.reply_text(
        text=message,
        reply_markup=keyboard,
        reply_to_message_id=update.reply_to_message_id,
    )
    add_user(update.from_user.id, update.from_user.username, update.from_user.language_code)
