import logging
from pathlib import Path

from django.conf import settings
from telegram import Bot, Update
from telegram.ext import Application

from feedback_bot.models import Bot as BotConfig
from feedback_bot.telegram.crud import get_bots_keys, get_bots_tokens
from feedback_bot.telegram.utils.cryptography import generate_bot_webhook_secret
from feedback_bot.utils.modules_loader import get_modules, load_modules

logger = logging.getLogger(__name__)


def build_feedback_bot_application(bot_config: BotConfig) -> Application:
    """
    Builds and configures a lightweight, request-scoped PTB Application
    for a feedback bot.
    """
    application = (
        Application.builder()
        .updater(None)
        .job_queue(None)
        .rate_limiter(None)
        .concurrent_updates(1)
        .token(bot_config.token)
        .build()
    )

    application.bot_data['bot_config'] = bot_config

    for module in load_modules(get_modules(Path(__file__).parent / 'modules')):
        if hasattr(module, 'HANDLERS'):
            application.add_handlers(module.HANDLERS)

    return application


async def setup_bots_webhooks() -> None:
    """Setup webhooks for bots."""
    logger.info('Bots webhooks setup...')

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

    bots_tokens = await get_bots_tokens()
    for bot_token in bots_tokens:
        ptb_bot = Bot(token=bot_token)
        await ptb_bot.delete_webhook()
    logger.info(f'Bots webhooks removed for {len(bots_tokens)} bots.')
