from collections.abc import Callable
from typing import Any

import regex as re
from pyrogram import Client, filters
from pyrogram.types import Message


def check_if_token_reply(_: Callable[..., Any], __: Client, message: Message) -> bool:
    return bool(
        re.search(r'^\d{8,20}:[A-Za-z0-9_-]{35}$', message.text)
        and message.reply_to_message.reply_markup
        and any(
            button.callback_data == 'main' or re.search(r'^mbt_\d+$', button.callback_data)
            for row in message.reply_to_message.reply_markup.inline_keyboard
            for button in row
        )
    )


def check_if_custom_message_reply(_: Callable[..., Any], __: Client, message: Message) -> bool:
    return bool(
        message.reply_to_message.reply_markup
        and any(
            re.search(r'^mb[mrcs]_\d+$', button.callback_data)
            for row in message.reply_to_message.reply_markup.inline_keyboard
            for button in row
        )
    )


is_token_reply = filters.create(check_if_token_reply)
is_custom_message_reply = filters.create(check_if_custom_message_reply)
