from plate import Plate
from pyrogram import Client, filters
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from src import BOT_ADMINS, DATA_DIR
from src.builder.db.crud import (
    TBot,
    add_to_whitelist,
    get_all_bots,
    get_bot,
    get_user,
    get_user_bots,
    get_whitelist,
    remove_bot,
    remove_from_whitelist,
    update_bot_status,
)
from src.builder.db.models.bot import Bot
from src.common.utils.filters import is_admin
from src.common.utils.i18n import localize
from src.common.utils.telegram_handlers import tg_exceptions_handler
from src.main import BOTS


@Client.on_message(filters.private & filters.command('manage') & is_admin(BOT_ADMINS))
@Client.on_callback_query(filters.regex('^manage$') & is_admin(BOT_ADMINS))
@tg_exceptions_handler
@localize
async def manage_command(_: Client, update: Message | CallbackQuery, i18n: Plate) -> None:
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(i18n('manage_bots'), callback_data='_manage_bots')],
            [InlineKeyboardButton(i18n('manage_users'), callback_data='manage_users')],
        ]
    )
    if isinstance(update, Message):
        await update.reply_text(i18n('select_manage_option'), reply_markup=keyboard)
    else:
        await update.message.edit_text(i18n('select_manage_option'), reply_markup=keyboard)


@Client.on_callback_query(filters.regex('^manage_users$') & is_admin(BOT_ADMINS))
@tg_exceptions_handler
@localize
async def list_users(_: Client, query: CallbackQuery, i18n: Plate) -> None:
    keyboard = [
        [InlineKeyboardButton(f'{user}', callback_data=f'manage_user_{user}')]
        for user in get_whitelist()
    ]
    keyboard.append([InlineKeyboardButton(i18n('back'), callback_data='manage')])
    await query.edit_message_text(i18n('select_user'), reply_markup=InlineKeyboardMarkup(keyboard))


@Client.on_callback_query(filters.regex(r'^manage_user_\d+$') & is_admin(BOT_ADMINS))
@tg_exceptions_handler
@localize
async def user_info(_: Client, query: CallbackQuery, i18n: Plate) -> None:
    user_id = int(query.data.split('_')[-1])
    user = get_user(user_id)
    info_text = (
        f"👤: <a href='tg://user?id={user_id}'>{getattr(user, 'user_name', user_id)}</a>\n"
        f'🆔: {user_id}\n'
    )
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    i18n('remove_user_and_bots'), callback_data=f'remove_user_{user_id}'
                )
            ],
            [InlineKeyboardButton(i18n('back'), callback_data='manage_users')],
        ]
    )
    await query.edit_message_text(info_text, reply_markup=keyboard)


@Client.on_callback_query(filters.regex(r'^remove_user_\d+$') & is_admin(BOT_ADMINS))
@tg_exceptions_handler
@localize
async def remove_user(_: Client, query: CallbackQuery, i18n: Plate) -> None:
    user_id = int(query.data.split('_')[-1])
    remove_from_whitelist(user_id)
    if get_user(user_id):
        for bot in get_user_bots(user_id):
            if bot.user_id in BOTS:
                await BOTS.pop(bot.user_id).stop()
            for file in DATA_DIR.glob(f'{bot.user_id}.*'):
                file.unlink(missing_ok=True)
            remove_bot(bot.user_id, user_id)
    await query.edit_message_text(
        i18n('user_removed'),
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton(i18n('back'), callback_data='manage_users')],
            ]
        ),
    )


@Client.on_message(
    filters.private & filters.command('whitelist')
    and filters.regex(r'^/whitelist\s+(\d+)$') & is_admin(BOT_ADMINS)
)
@tg_exceptions_handler
@localize
async def add_user(_: Client, message: Message, i18n: Plate) -> None:
    user_id = int(message.matches[0].group(1))
    add_to_whitelist(user_id)
    await message.reply_text(i18n('user_whitelisted'))


@Client.on_callback_query(filters.regex('^_manage_bots$') & is_admin(BOT_ADMINS))
@tg_exceptions_handler
@localize
async def list_bots(_: Client, query: CallbackQuery, i18n: Plate) -> None:
    bots = get_all_bots()
    keyboard = [
        [
            InlineKeyboardButton(
                f'{bot.name} - {bot.username}', callback_data=f'manage_bot_{bot.user_id}'
            )
        ]
        for bot in bots
    ]
    keyboard.append([InlineKeyboardButton(i18n('back'), callback_data='main')])
    await query.edit_message_text(i18n('select_bot'), reply_markup=InlineKeyboardMarkup(keyboard))


@Client.on_callback_query(
    (filters.regex(r'^manage_bot_\d+$') | filters.regex(r'^toggle_bot_\d+$')) & is_admin(BOT_ADMINS)
)
@tg_exceptions_handler
@localize
async def bot_info(_: Client, query: CallbackQuery, i18n: Plate) -> None:
    bot_id = query.data.split('_')[-1]
    bot: TBot | Bot | None = (
        update_bot_status(bot_id) if query.data.startswith('toggle_bot') else get_bot(bot_id)
    )
    assert bot is not None
    bot_owner = get_user(bot.owner)
    assert bot_owner is not None
    info_text = (
        f"🤖: {bot.name} @{bot.username} {bot_id}\n"
        f"👤: <a href='tg://user?id={bot.owner}'>{bot_owner.user_name}</a>\n"
        f"💡: {'✅' if bot.enabled else '❌'}\n"
    )
    if bot.created_at:
        info_text += f"🗓️: {bot.created_at.strftime('%Y-%m-%d')}"
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    i18n(
                        'bot_toggle_status',
                        username=bot.username,
                        status=not bot.enabled,
                    ),
                    callback_data=f'toggle_bot_{bot_id}',
                )
            ],
            [InlineKeyboardButton(i18n('back'), callback_data='_manage_bots')],
        ]
    )

    await query.edit_message_text(info_text, reply_markup=keyboard)
