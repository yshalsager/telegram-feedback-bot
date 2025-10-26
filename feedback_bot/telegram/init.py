import fcntl
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from django.conf import settings
from django_asgi_lifespan.types import LifespanManager
from telegram import BotCommandScopeAllPrivateChats, Update

from feedback_bot.telegram.builder.bot import get_ptb_application, load_builder_modules
from feedback_bot.telegram.utils.cryptography import generate_bot_webhook_secret
from feedback_bot.telegram.utils.restart import handle_restart

logger = logging.getLogger(__name__)
LOCK_PATH = Path(os.getenv('PTB_WEBHOOK_LOCK', 'ptb-webhook.lock'))


@asynccontextmanager
async def ptb_lifespan_manager() -> LifespanManager:  # noqa: PLR0915
    logger.info('ASGI Lifespan: Starting up...')
    lock_fd = None
    lock_acquired = True
    try:
        LOCK_PATH.touch(exist_ok=True)
        lock_fd = os.open(str(LOCK_PATH), os.O_RDWR)
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except ModuleNotFoundError:
        logger.warning('ASGI Lifespan: fcntl unavailable, skipping webhook lock')
    except BlockingIOError:
        logger.info('ASGI Lifespan: PTB startup handled by another worker')
        lock_acquired = False
    except Exception as exc:  # noqa: BLE001
        logger.warning('ASGI Lifespan: Failed to lock PTB startup: %s', exc)
        lock_acquired = False

    if not lock_acquired:
        try:
            yield {}
        finally:
            if lock_fd is not None:
                os.close(lock_fd)
        return

    ptb_application = get_ptb_application()
    state = {'ptb_application': ptb_application, 'lock_fd': lock_fd}

    try:
        commands = load_builder_modules()
        async with ptb_application:
            await ptb_application.start()
            await ptb_application.bot.set_webhook(
                url=f'{settings.TELEGRAM_BUILDER_BOT_WEBHOOK_URL}/api/webhook/{settings.TELEGRAM_BUILDER_BOT_WEBHOOK_PATH}',
                secret_token=generate_bot_webhook_secret(
                    settings.TELEGRAM_BUILDER_BOT_WEBHOOK_PATH
                ),
                allowed_updates=Update.ALL_TYPES,
            )
            logger.info('ASGI Lifespan: Main bot webhook is set.')
            await handle_restart(ptb_application)
            await ptb_application.bot.set_my_commands(
                commands, scope=BotCommandScopeAllPrivateChats()
            )
            logger.info('ASGI Lifespan: Setting up webhooks for bots...')
            from feedback_bot.telegram.feedback_bot.bot import setup_bots_webhooks  # noqa: PLC0415

            await setup_bots_webhooks()
            logger.info('ASGI Lifespan: PTB application started and all webhooks are set.')
            yield state

    finally:
        from feedback_bot.telegram.feedback_bot.bot import remove_bots_webhooks  # noqa: PLC0415

        await remove_bots_webhooks()
        await state['ptb_application'].bot.delete_webhook()
        logger.info('ASGI Lifespan: Main bot webhook removed.')
        await state['ptb_application'].stop()
        await state['ptb_application'].shutdown()
        logger.info('ASGI Lifespan: PTB application stopped.')
        lock_fd = state.get('lock_fd')
        if lock_fd is not None:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
            except Exception as exc:  # noqa: BLE001
                logger.warning('ASGI Lifespan: Failed to unlock PTB startup: %s', exc)
            os.close(lock_fd)
