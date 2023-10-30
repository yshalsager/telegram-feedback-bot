import logging
from asyncio import sleep
from collections.abc import Callable
from functools import wraps
from typing import Any, cast

from httpx import ReadError
from telegram import Update
from telegram.constants import ChatAction
from telegram.error import BadRequest, Forbidden, RetryAfter, TimedOut
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from feedbackbot import application
from feedbackbot.db.curd import remove_chat_from_db

logger = logging.getLogger(__name__)

TELEGRAM_FATAL_ERRORS = (
    "bot was blocked by the user",
    "user is deactivated",
    "bot was kicked from the group chat",
    "bot was kicked from the supergroup chat",
    "bot was kicked from the channel chat",
    "bot is not a member of the channel chat",
    "Chat not found",
    "Not enough rights to send text messages to the chat",
    "the group chat was deleted",
)


def command_handler(command: str, *args: Any, **kwargs: Any) -> Callable[..., Any]:
    def decorator(
        func: Callable[..., Any],
    ) -> Callable[..., Any]:
        if args or kwargs:
            application.add_handler(CommandHandler(command, func, *args, **kwargs))
        else:
            application.add_handler(MessageHandler(filters.Regex(rf"^/{command}(?:@\S+)?$"), func))
        return cast(Callable[..., Any], func)

    return decorator


def send_action(action: ChatAction) -> Callable[..., Any]:
    """Sends `action` while processing func command."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def command_func(
            update: Update,
            context: ContextTypes.DEFAULT_TYPE,
            *args: Any,
            **kwargs: Any,
        ) -> Callable[..., Any]:
            assert update.effective_message is not None
            await context.bot.send_chat_action(
                chat_id=update.effective_message.chat_id, action=action
            )
            return cast(Callable[..., Any], await func(update, context, *args, **kwargs))

        return command_func

    return decorator


def tg_exceptions_handler(func: Callable[..., Any]) -> Callable[..., Any]:  # noqa: C901
    @wraps(func)
    async def exceptions_handler_func(  # type: ignore[return]
        *args: Any, **kwargs: Any
    ) -> Callable[..., Any]:
        update: Update | None = None
        context: ContextTypes.DEFAULT_TYPE | None = None
        if len(args) == 2:
            update, context = args[:2]
        try:
            return cast(Callable[..., Any], await func(*args, **kwargs))
        except (ReadError, TimedOut):
            pass
        except BadRequest as err:
            if (
                "Message is not modified" in err.message
                or "Query is too old" in err.message
                or "Message can't be deleted for everyone" in err.message
            ):
                pass
            else:
                raise err
        except Forbidden as err:
            if any(error in err.message for error in TELEGRAM_FATAL_ERRORS):
                if len(args) == 2 and update and context:
                    assert update is not None
                    assert update.effective_chat is not None
                    removed_chat_successfully = remove_chat_from_db(update.effective_chat.id)
                    logger.info(
                        f"User {update.effective_chat.id} was removed. Removed chat: {removed_chat_successfully}"
                    )
            else:
                raise err
        except RetryAfter as error:
            await sleep(error.retry_after)
            return await exceptions_handler_func(*args, **kwargs)
        except Exception as err:
            raise err

    return exceptions_handler_func
