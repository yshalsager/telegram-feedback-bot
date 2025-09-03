import logging
from contextlib import asynccontextmanager

from django.conf import settings
from django_asgi_lifespan.types import LifespanManager
from telegram import Bot, Update
from telegram.ext import Application

from feedback_bot.telegram.builder.modules import ALL_MODULES
from feedback_bot.telegram.utils.cryptography import generate_bot_webhook_secret
from feedback_bot.telegram.utils.modules_loader import load_modules

logging.getLogger('httpx').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


async def setup_bots_webhooks() -> None:
    """Setup webhooks for bots."""
    logger.info('Bots webhooks setup...')
    from feedback_bot.telegram.builder.crud import get_bots_keys  # noqa: PLC0415

    bots_keys = await get_bots_keys()
    for bot_uuid, bot_token in bots_keys:
        ptb_bot = Bot(token=bot_token)
        webhook_url = f'{settings.TELEGRAM_BUILDER_BOT_WEBHOOK_URL}/api/webhook/{bot_uuid}/'
        await ptb_bot.set_webhook(
            webhook_url,
            secret_token=generate_bot_webhook_secret(str(bot_uuid)),
            allowed_updates=Update.ALL_TYPES,
        )
    logger.info(f'Bots webhooks setup done for {len(bots_keys)} bots.')


async def remove_bots_webhooks() -> None:
    """Remove webhooks for bots."""
    logger.info('Removing bots webhooks...')
    from feedback_bot.telegram.builder.crud import get_bots_tokens  # noqa: PLC0415

    bots_tokens = await get_bots_tokens()
    for bot_token in bots_tokens:
        ptb_bot = Bot(token=bot_token)
        await ptb_bot.delete_webhook()
    logger.info(f'Bots webhooks removed for {len(bots_tokens)} bots.')


# Here we set updater to None because we want our custom webhook server to handle the updates
# and hence we don't need an Updater instance
ptb_application = (
    Application.builder().token(settings.TELEGRAM_BUILDER_BOT_TOKEN).updater(None).build()
)


@asynccontextmanager
async def ptb_lifespan_manager() -> LifespanManager:
    logger.info('ASGI Lifespan: Starting up...')
    state = {'ptb_application': ptb_application}

    try:
        for module in load_modules(ALL_MODULES):
            if hasattr(module, 'HANDLERS'):
                ptb_application.add_handlers(module.HANDLERS)
        async with ptb_application:
            await ptb_application.start()
            await ptb_application.bot.set_webhook(
                url=f'{settings.TELEGRAM_BUILDER_BOT_WEBHOOK_URL}/api/webhook/{settings.TELEGRAM_BUILDER_BOT_WEBHOOK_PATH}',
                secret_token=settings.TELEGRAM_BUILDER_BOT_WEBHOOK_SECRET,
                allowed_updates=Update.ALL_TYPES,
            )
            logger.info('ASGI Lifespan: Main bot webhook is set.')

            logger.info('ASGI Lifespan: Setting up webhooks for bots...')
            await setup_bots_webhooks()

            logger.info('ASGI Lifespan: PTB application started and all webhooks are set.')
            yield state

    finally:
        await remove_bots_webhooks()
        await state['ptb_application'].bot.delete_webhook()
        logger.info('ASGI Lifespan: Main bot webhook removed.')
        await state['ptb_application'].stop()
        await state['ptb_application'].shutdown()
        logger.info('ASGI Lifespan: PTB application stopped.')
