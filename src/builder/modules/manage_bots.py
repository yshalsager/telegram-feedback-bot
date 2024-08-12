from plate import Plate
from pyrogram import Client, filters
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from src import DATA_DIR
from src.builder.db.crud import (
    delete_bot_group,
    get_bot,
    get_user_bots,
    remove_bot,
    update_bot_confirmations,
    update_bot_messages,
)
from src.builder.db.models.bot import Bot
from src.builder.utils.filters import is_custom_message_reply, is_whitelisted_user
from src.builder.utils.keyboards import get_main_menu_keyboard, get_update_bot_messages_keyboard
from src.common.utils.i18n import localize
from src.common.utils.telegram_handlers import tg_exceptions_handler
from src.main import BOTS


@Client.on_callback_query(is_whitelisted_user() & filters.regex(r'^manage_bots$'))
@tg_exceptions_handler
@localize
async def manage_bots(_: Client, update: CallbackQuery, i18n: Plate) -> None:
    user_bots = get_user_bots(update.from_user.id)
    if not user_bots:
        await update.answer(i18n('no_bots'))
        return
    await update.message.edit_text(
        i18n('select_bot'),
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        f'{bot.name} - @({bot.username})',
                        callback_data=f'mb_{bot.user_id}',
                    )
                ]
                for bot in user_bots
            ]
            + [[InlineKeyboardButton(f"{i18n('back_to_main_menu')}", callback_data='main')]]
        ),
    )


@Client.on_callback_query(is_whitelisted_user() & filters.regex(r'^mb_(\d+)$'))
@tg_exceptions_handler
@localize
async def show_bot_manage_options(_: Client, update: CallbackQuery, i18n: Plate) -> None:
    bot_id = update.matches[0].group(1)
    bot: Bot | None = get_bot(bot_id)
    if not bot:
        await update.answer(i18n('no_bots'))
        return
    await update.message.edit_text(
        i18n('select_manage_option'),
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton(f"{i18n('delete_bot')}", callback_data=f'mbd_{bot_id}')],
                [
                    InlineKeyboardButton(
                        f"{i18n('change_bot_token')}", callback_data=f'mbt_{bot_id}'
                    )
                ],
                [
                    InlineKeyboardButton(
                        f"{i18n('change_bot_group')}", callback_data=f'mbg_{bot_id}'
                    )
                ],
                [
                    InlineKeyboardButton(
                        f"{i18n('bot_confirmations')}", callback_data=f'mbc_{bot_id}'
                    )
                ],
                [
                    InlineKeyboardButton(
                        f"{i18n('change_bot_start_message')}", callback_data=f'mbm_{bot_id}'
                    )
                ],
                [
                    InlineKeyboardButton(
                        f"{i18n('change_bot_receive_message')}", callback_data=f'mbrc_{bot_id}'
                    )
                ],
                [
                    InlineKeyboardButton(
                        f"{i18n('change_bot_sent_message')}", callback_data=f'mbsm_{bot_id}'
                    )
                ],
                [InlineKeyboardButton(f"{i18n('back_to_main_menu')}", callback_data='main')],
            ]
        ),
    )


@Client.on_callback_query(is_whitelisted_user() & filters.regex(r'^mbd_\d+$'))
@tg_exceptions_handler
@localize
async def delete_bot(_: Client, update: CallbackQuery, i18n: Plate) -> None:
    bot_id = update.data.split('_')[-1]
    if not get_bot(bot_id):
        await update.answer(i18n('no_bots'))
        return
    await update.answer()
    if int(bot_id) in BOTS:
        await BOTS[int(bot_id)].stop()
    for file in DATA_DIR.glob(f'{bot_id}.*'):
        file.unlink(missing_ok=True)
    message = (
        i18n('bot_deleted_success')
        if remove_bot(bot_id, update.from_user.id)
        else i18n('bot_deleted_error')
    )
    await update.message.edit_text(message, reply_markup=get_main_menu_keyboard(i18n))


@Client.on_callback_query(is_whitelisted_user() & filters.regex(r'^mbg_\d+$'))
@tg_exceptions_handler
@localize
async def change_group(_: Client, update: CallbackQuery, i18n: Plate) -> None:
    bot_id = update.data.split('_')[-1]
    bot: Bot | None = get_bot(bot_id)
    if not bot:
        await update.answer(i18n('no_bots'))
        return
    await update.answer()
    await update.message.edit_text(
        i18n('change_group_help'),
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        f"{i18n('unlink_bot_from_group')}", callback_data=f'mbgu_{bot_id}'
                    )
                ],
                [InlineKeyboardButton(f"{i18n('back_to_main_menu')}", callback_data='main')],
            ]
        ),
    )


@Client.on_callback_query(is_whitelisted_user() & filters.regex(r'^mbgu_\d+$'))
@tg_exceptions_handler
@localize
async def unlink_bot_from_group(client: Client, update: CallbackQuery, i18n: Plate) -> None:
    bot_id = update.data.split('_')[-1]
    bot: Bot | None = get_bot(bot_id)
    if not bot:
        await update.answer(i18n('no_bots'))
        return
    group_to_leave = bot.group
    if not group_to_leave:
        await update.answer(i18n('bot_has_no_group'))
        return
    await update.answer()
    is_unlinked: bool = delete_bot_group(bot_id)
    if is_unlinked:
        await client.leave_chat(group_to_leave)
        message = i18n('unlink_bot_from_group_success')
    else:
        message = i18n('unlink_bot_from_group_error')
    await update.message.edit_text(message, reply_markup=get_main_menu_keyboard(i18n))


@Client.on_callback_query(is_whitelisted_user() & filters.regex(r'^mbc_(\d+)$'))
@tg_exceptions_handler
@localize
async def toggle_bot_confirmations(_: Client, update: CallbackQuery, i18n: Plate) -> None:
    bot_id = update.data.split('_')[-1]
    bot: Bot | None = get_bot(bot_id)
    if not bot:
        await update.answer(i18n('no_bots'))
        return
    update_bot_confirmations(bot.user_id)
    await update.answer(
        f'{i18n("bot_confirmations")}: {"✅" if bot.bot_settings.confirmations else "❌"}'
    )
    return


@Client.on_callback_query(is_whitelisted_user() & filters.regex(r'^mbt_\d+$'))
@tg_exceptions_handler
@localize
# user should reply to this message with new token
async def change_token(_: Client, update: CallbackQuery, i18n: Plate) -> None:
    bot_id = update.data.split('_')[-1]
    bot: Bot | None = get_bot(bot_id)
    if not bot:
        await update.answer(i18n('no_bots'))
        return
    await update.answer()
    await update.message.edit_text(
        i18n('reply_with_token'), reply_markup=get_main_menu_keyboard(i18n)
    )


# TODO refactor to use replymarkup with emoji to allow force reply
@Client.on_callback_query(is_whitelisted_user() & filters.regex(r'^mb(?:m|rc|sm)_\d+$'))
@tg_exceptions_handler
@localize
async def reply_with_message(_: Client, update: CallbackQuery, i18n: Plate) -> None:
    choose, bot_id = update.data.split('_')
    bot: Bot | None = get_bot(bot_id)
    if not bot:
        await update.answer(i18n('no_bots'))
        return
    await update.answer()
    await update.message.edit_text(
        i18n('reply_with_new_message'),
        reply_markup=get_update_bot_messages_keyboard(bot_id, choose, i18n),
    )


message_type_to_key: dict[str, str] = {
    'm': 'start_message',
    'rc': 'received_message',
    'sm': 'sent_message',
}


@Client.on_message(
    is_whitelisted_user() & filters.private & filters.text & filters.reply & is_custom_message_reply
)
@tg_exceptions_handler
@localize
async def handle_custom_message(_: Client, message: Message, i18n: Plate) -> None:
    callback_data = next(
        (
            button.callback_data
            for row in message.reply_to_message.reply_markup.inline_keyboard
            for button in row
            if button.text.startswith('→')
        ),
        None,
    )
    if not callback_data:
        return

    try:
        message_type, bot_id_str = callback_data.split('_')[0][2:], callback_data.split('_')[-1]
        if message_type not in message_type_to_key:
            return
        bot_id = int(bot_id_str)
        bot: Bot | None = get_bot(bot_id)
        if not bot:
            return
    except (ValueError, IndexError):
        return
    message_property = message_type_to_key[message_type]
    updated = update_bot_messages(bot_id, **{message_property: message.text})
    await message.reply_to_message.edit_text(
        i18n('new_message_success') if updated else i18n('new_message_error'),
        reply_markup=get_main_menu_keyboard(i18n),
    )
