from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast

from telegram import Update
from telegram.ext import ContextTypes

from feedbackbot import TELEGRAM_CHAT_ID
from feedbackbot.db.curd import add_chat_to_db, add_topic, get_topic
from feedbackbot.utils.telegram import get_chat_type

F = TypeVar("F", bound=Callable[..., Any])


def add_new_chat_to_db(func: F) -> F:
    @wraps(func)
    async def wrapper(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args: list, **kwargs: dict
    ) -> F:
        assert update.effective_chat is not None
        assert update.effective_chat.id is not None
        assert (update.effective_chat.full_name or update.effective_chat.title) is not None
        chat_title = update.effective_chat.full_name or update.effective_chat.title
        assert chat_title is not None
        add_chat_to_db(
            update.effective_chat.id,
            chat_title,
            get_chat_type(update),
        )
        if not get_topic(update.effective_chat.id):
            forum_topic = await context.bot.create_forum_topic(TELEGRAM_CHAT_ID, chat_title)
            await context.bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                message_thread_id=forum_topic.message_thread_id,
                text=chat_title,
            )
            add_topic(update.effective_chat.id, forum_topic.message_thread_id)
        return cast(F, await func(update, context, *args, **kwargs))

    return cast(F, wrapper)
