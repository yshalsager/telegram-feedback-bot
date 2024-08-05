from plate import Plate
from pyrogram import Client, filters
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)

from src import BOT_ADMINS
from src.builder.db.crud import get_all_bots, update_bot_status
from src.builder.db.models.bot import Bot
from src.common.utils.filters import is_admin
from src.common.utils.i18n import localize
from src.common.utils.telegram_handlers import tg_exceptions_handler


async def change_bot_status(update: InlineQuery) -> None:
    choices = [
        InlineQueryResultArticle(
            title=bot.name,
            input_message_content=InputTextMessageContent(
                message_text=f"🤖 @{bot.username} by <a href='tg://user?id={bot.owner}'>{bot.owner}</a>\n\n"
                f"Enabled: {'✅' if bot.enabled else '❌'}",
            ),
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton('Toggle', callback_data=f'toggle_bot_{bot.user_id}')]]
            ),
        )
        for bot in get_all_bots()
    ]
    await update.answer(results=choices, cache_time=1)


@Client.on_inline_query()
@tg_exceptions_handler
async def inline(_: Client, update: InlineQuery) -> None:
    if update.from_user.id not in BOT_ADMINS:
        return
    query = update.query.strip()
    if query.lower() == 'manage':
        await change_bot_status(update)
        return


@Client.on_callback_query(filters.regex(r'^toggle_bot_\d+$') & is_admin(BOT_ADMINS))
@tg_exceptions_handler
@localize
async def toggle_bot(_: Client, update: CallbackQuery, i18n: Plate) -> None:
    bot_id = update.data.split('_')[-1]
    bot: Bot | None = update_bot_status(bot_id)
    if not bot:
        return
    await update.edit_message_text(
        i18n(
            'bot_toggle_status',
            username=bot.username,
            status=bot.enabled,
        )
    )
