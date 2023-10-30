from typing import cast

import regex as re
from telegram import Update
from telegram.constants import ChatType

escape_chars = r"\_*[]()~`>#+-={}.!"


def escape_markdown_v2(text: str) -> str:
    """
    A modified version of `escape_markdown` from `telegram.helpers` that doesn't escape markdown v2 spoiler
    :param text: message text to escape
    :return: escaped message text
    """
    return cast(str, re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", text))


CHAT_TYPES = {ChatType.PRIVATE: 0, ChatType.GROUP: 1, ChatType.CHANNEL: 2}


def get_chat_type(update: Update) -> int:
    chat = update.effective_chat
    assert chat is not None
    return CHAT_TYPES[chat.type]


def get_reply_to_message_id(update: Update) -> int | None:
    assert update.effective_message is not None
    return (
        update.effective_message.reply_to_message.id
        if update.effective_message.reply_to_message
        and update.effective_message.reply_to_message.id
        else None
    )
