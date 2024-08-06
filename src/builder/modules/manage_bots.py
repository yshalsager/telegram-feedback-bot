from plate import Plate
from pyrogram import Client, filters
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from src.builder.db.crud import (
    TBot,
    delete_bot_group,
    get_bot,
    get_user_bots,
    remove_bot,
    update_bot_messages,
)
from src.builder.utils.filters import is_custom_message_reply
from src.builder.utils.keyboards import get_main_menu_keyboard, get_update_bot_messages_keyboard
from src.common.utils.i18n import localize
from src.common.utils.telegram_handlers import tg_exceptions_handler


@Client.on_callback_query(filters.regex(r'^manage_bots$'))
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


@Client.on_callback_query(filters.regex(r'^mb_\d+$'))
@tg_exceptions_handler
@localize
async def show_bot_manage_options(_: Client, update: CallbackQuery, i18n: Plate) -> None:
    bot_id = update.data.split('_')[-1]
    if not get_bot(bot_id):
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


@Client.on_callback_query(filters.regex(r'^mbd_\d+$'))
@tg_exceptions_handler
@localize
async def delete_bot(_: Client, update: CallbackQuery, i18n: Plate) -> None:
    bot_id = update.data.split('_')[-1]
    if not get_bot(bot_id):
        await update.answer(i18n('no_bots'))
        return
    await update.answer()
    message = (
        i18n('bot_deleted_success')
        if remove_bot(bot_id, update.from_user.id)
        else i18n('bot_deleted_error')
    )
    await update.message.edit_text(message, reply_markup=get_main_menu_keyboard(i18n))


@Client.on_callback_query(filters.regex(r'^mbg_\d+$'))
@tg_exceptions_handler
@localize
async def change_group(_: Client, update: CallbackQuery, i18n: Plate) -> None:
    bot_id = update.data.split('_')[-1]
    bot: TBot | None = get_bot(bot_id)
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


@Client.on_callback_query(filters.regex(r'^mbgu_\d+$'))
@tg_exceptions_handler
@localize
async def unlink_bot_from_group(client: Client, update: CallbackQuery, i18n: Plate) -> None:
    bot_id = update.data.split('_')[-1]
    bot: TBot | None = get_bot(bot_id)
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


@Client.on_callback_query(filters.regex(r'^mbt_\d+$'))
@tg_exceptions_handler
@localize
# user should reply to this message with new token
async def change_token(_: Client, update: CallbackQuery, i18n: Plate) -> None:
    bot_id = update.data.split('_')[-1]
    bot: TBot | None = get_bot(bot_id)
    if not bot:
        await update.answer(i18n('no_bots'))
        return
    await update.answer()
    await update.message.edit_text(
        i18n('reply_with_token'), reply_markup=get_main_menu_keyboard(i18n)
    )


@Client.on_callback_query(filters.regex(r'^mb[mrcs]+_\d+$'))
@tg_exceptions_handler
@localize
async def reply_with_message(_: Client, update: CallbackQuery, i18n: Plate) -> None:
    choose, bot_id = update.data.split('_')
    bot: TBot | None = get_bot(bot_id)
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


@Client.on_message(filters.private & filters.text & filters.reply & is_custom_message_reply)
@tg_exceptions_handler
@localize
async def handle_custom_message(_: Client, message: Message, i18n: Plate) -> None:
    callback_data = message.reply_to_message.reply_markup.inline_keyboard[0][0].callback_data
    message_type = callback_data.split('_')[0][2:]
    if message_type not in message_type_to_key:
        return
    bot_id = int(callback_data.split('_')[-1])
    bot: TBot | None = get_bot(bot_id)
    if not bot:
        return
    message_property = message_type_to_key[message_type]
    updated = update_bot_messages(bot_id, **{message_property: message.text})
    await message.reply_to_message.edit_text(
        i18n('new_message_success') if updated else i18n('new_message_error'),
        reply_markup=get_main_menu_keyboard(i18n),
    )
