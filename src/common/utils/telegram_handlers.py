import logging
from asyncio import sleep
from collections.abc import Callable
from functools import wraps
from typing import Any, cast

from pyrogram import Client, ContinuePropagation, StopPropagation
from pyrogram.errors import (
    BadRequest,
    Forbidden,
    InlineResultExpired,
    MessageNotModified,
    SlowmodeWait,
)
from pyrogram.types import Message

from src import BOT_TOKEN
from src.bot.db.crud import remove_chat_from_db
from src.bot.db.session import session_scope
from src.builder.modules.errors import error_handler

logger = logging.getLogger(__name__)

TELEGRAM_FATAL_ERRORS = (
    'bot was blocked by the user',
    'user is deactivated',
    'bot was kicked from the group chat',
    'bot was kicked from the supergroup chat',
    'bot was kicked from the channel chat',
    'bot is not a member of the channel chat',
    'Chat not found',
    'Not enough rights to send text messages to the chat',
    'the group chat was deleted',
)


def tg_exceptions_handler(func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(func)
    async def exceptions_handler_func(  # type: ignore[return]
        *args: Any, **kwargs: Any
    ) -> Callable[..., Any]:
        client: Client | None = None
        message: Message | None = None
        if len(args) == 2:
            client, message = args[:2]
        try:
            return cast(Callable[..., Any], await func(*args, **kwargs))
        except (MessageNotModified, InlineResultExpired, ContinuePropagation, StopPropagation):
            pass
        except Forbidden as err:
            if any(error in err.value for error in TELEGRAM_FATAL_ERRORS):
                if len(args) == 2 and client and message and client.bot_token != BOT_TOKEN:
                    with session_scope(client.me.id) as session:
                        removed_chat_successfully = remove_chat_from_db(session, message.chat.id)
                    logger.info(
                        f'User {message.chat.id} was removed. Removed chat: {removed_chat_successfully}'
                    )
            else:
                await error_handler(err, client, message)
        except SlowmodeWait as error:
            await sleep(error.value + 1)
            return await exceptions_handler_func(*args, **kwargs)
        except BadRequest as err:
            await error_handler(err, client, message)
        except Exception as err:  # noqa: BLE001
            await error_handler(err, client, message)

    return exceptions_handler_func
