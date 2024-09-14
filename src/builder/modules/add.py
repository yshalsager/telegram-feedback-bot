from plate import Plate
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import (
    CallbackQuery,
    ForceReply,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    User,
)

from src import API_HASH, API_ID, BOTS, DATA_DIR, NEW_BOT_ADMIN_APPROVAL
from src.bot.db.session import create_db
from src.builder.db.crud import add_bot, get_bot
from src.builder.db.models.bot import Bot
from src.builder.utils.filters import is_token_reply, is_whitelisted_user
from src.builder.utils.keyboards import get_main_menu_keyboard
from src.common.utils.i18n import localize
from src.common.utils.telegram import get_bot_id
from src.common.utils.telegram_handlers import tg_exceptions_handler

package_name = __package__.split('.')[0]


@Client.on_callback_query(is_whitelisted_user() & filters.regex('^add_bot$'))
@tg_exceptions_handler
@localize
async def add(_: Client, update: CallbackQuery, i18n: Plate) -> None:
    message = await update.message.edit_text(
        i18n('reply_with_token'),
        reply_markup=ForceReply(selective=True),
    )
    await message.reply_text(i18n('back_to_main_menu'), reply_markup=get_main_menu_keyboard(i18n))


@Client.on_message(
    is_whitelisted_user() & filters.private & filters.text & filters.reply & is_token_reply
)
@tg_exceptions_handler
@localize
async def handle_token(_: Client, message: Message, i18n: Plate) -> None:
    old_bot_id: int = int(message.text.split(':')[0])
    old_bot: Client | None = BOTS.get(old_bot_id)
    if old_bot:
        await old_bot.stop()
    reply_message = await message.reply_to_message.reply_text(
        i18n('checking_token'), reply_to_message_id=message.reply_to_message.id
    )
    bot_token = message.text.strip()
    bot_id = get_bot_id(bot_token)
    bot_obj: Bot | None = get_bot(bot_id)
    async with Client(
        str(bot_id),
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=bot_token,
        in_memory=True,
    ) as test_client:
        try:
            bot: User = await test_client.get_me()
            add_bot(
                bot.id,
                bot.full_name,
                bot.username,
                bot_token.split(':')[1],
                message.chat.id,
                enabled=not NEW_BOT_ADMIN_APPROVAL,
            )
            await reply_message.edit_text(
                i18n('valid_token', username=bot.username),
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                f"{i18n('add_bot_to_group')}",
                                url=f'https://t.me/{bot.username}?startgroup=true',
                            ),
                            InlineKeyboardButton(
                                f"{i18n('manage_bots')}", callback_data='manage_bots'
                            ),
                            InlineKeyboardButton(
                                f"{i18n('back_to_main_menu')}", callback_data='main'
                            ),
                        ]
                    ]
                ),
            )
        except Exception as err:
            await reply_message.edit_text(
                i18n('invalid_token'),
                reply_markup=get_main_menu_keyboard(i18n),
            )
            if old_bot:
                await old_bot.start()
            raise err
    await message.delete()
    if bot_obj:
        await message.reply_text(
            i18n('bot_already_added'),
            reply_markup=get_main_menu_keyboard(i18n),
        )
        return
    if not NEW_BOT_ADMIN_APPROVAL:
        new_bot = Client(
            str(bot_id),
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=bot_token,
            plugins={'root': f'{package_name}.bot.modules'},
            parse_mode=ParseMode.HTML,
            workdir=DATA_DIR,
        )
        create_db(bot_id)
        await new_bot.start()
        if old_bot:
            del BOTS[old_bot_id]
        BOTS.update({bot_id: new_bot})
