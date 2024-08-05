from plate import Plate
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_main_menu_keyboard(i18n: Plate) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(f"{i18n('back_to_main_menu')}", callback_data='main'),
            ]
        ]
    )


def get_update_bot_messages_keyboard(bot_id: str, choose: str, i18n: Plate) -> InlineKeyboardMarkup:
    buttons = [
        ('change_bot_start_message', f'mbm_{bot_id}'),
        ('change_bot_receive_message', f'mbrc_{bot_id}'),
        ('change_bot_sent_message', f'mbsm_{bot_id}'),
    ]

    keyboard = [
        [
            InlineKeyboardButton(
                f"{'→ ' if choose == callback_data.split('_')[0] else ''}{i18n(text)}",
                callback_data=callback_data,
            )
        ]
        for text, callback_data in buttons
    ]

    keyboard.append([InlineKeyboardButton(f"{i18n('back_to_main_menu')}", callback_data='main')])

    return InlineKeyboardMarkup(keyboard)
