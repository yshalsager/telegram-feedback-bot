import logging
from contextlib import asynccontextmanager

from django.conf import settings
from django_asgi_lifespan.types import LifespanManager
from telegram import Update

from feedback_bot.telegram.builder.bot import load_builder_modules, ptb_application

logger = logging.getLogger(__name__)


@asynccontextmanager
async def ptb_lifespan_manager() -> LifespanManager:
    logger.info('ASGI Lifespan: Starting up...')
    state = {'ptb_application': ptb_application}

    try:
        load_builder_modules()
        async with ptb_application:
            await ptb_application.start()
            await ptb_application.bot.set_webhook(
                url=f'{settings.TELEGRAM_BUILDER_BOT_WEBHOOK_URL}/api/webhook/{settings.TELEGRAM_BUILDER_BOT_WEBHOOK_PATH}',
                secret_token=settings.TELEGRAM_BUILDER_BOT_WEBHOOK_SECRET,
                allowed_updates=Update.ALL_TYPES,
            )
            logger.info('ASGI Lifespan: Main bot webhook is set.')
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
