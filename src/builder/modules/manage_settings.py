from plate import Plate
from pyrogram import Client, filters
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from src.builder.db.crud import get_user, update_user_language
from src.builder.utils.filters import is_whitelisted_user
from src.common.utils.i18n import languages, localize, plate
from src.common.utils.telegram_handlers import tg_exceptions_handler


@Client.on_callback_query(is_whitelisted_user() & filters.regex(r'^manage_settings$'))
@tg_exceptions_handler
@localize
async def manage_settings(_: Client, update: CallbackQuery, i18n: Plate) -> None:
    user = get_user(update.from_user.id)
    if not user:
        await update.answer(i18n('user_not_found'))
        return
    await update.message.edit_text(
        i18n('select_setting_to_change'),
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        f"{i18n('change_language')}", callback_data='change_language'
                    )
                ],
                [InlineKeyboardButton(f"{i18n('back_to_main_menu')}", callback_data='main')],
            ]
        ),
    )


def _create_language_button(locale: str) -> InlineKeyboardButton:
    lang_code = locale.split('_')[0]
    lang = languages[lang_code]
    name = lang['name']
    native_name = lang['nativeName']
    button_text = name if name.lower() == native_name.lower() else f'{name} - {native_name}'
    return InlineKeyboardButton(
        button_text,
        callback_data=f'set_lang_{lang_code}',
    )


@Client.on_callback_query(is_whitelisted_user() & filters.regex(r'^change_language$'))
@tg_exceptions_handler
@localize
async def change_language(_: Client, update: CallbackQuery, i18n: Plate) -> None:
    buttons = [[_create_language_button(locale)] for locale in plate.locales]
    buttons.append([InlineKeyboardButton(i18n('back'), callback_data='manage_settings')])
    await update.message.edit_text(
        i18n('select_language'),
        reply_markup=InlineKeyboardMarkup(buttons),
    )


@Client.on_callback_query(is_whitelisted_user() & filters.regex(r'^set_lang_\w+$'))
@tg_exceptions_handler
@localize
async def set_language(_: Client, update: CallbackQuery, i18n: Plate) -> None:
    lang_code = update.data.split('_')[-1]
    if update_user_language(update.from_user.id, lang_code):
        await update.answer(i18n('language_updated'))
        await manage_settings(_, update)
    else:
        await update.answer(i18n('language_update_failed'))
