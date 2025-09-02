import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import cast

from django.conf import settings
from django_asgi_lifespan.types import LifespanManager
from telegram import Bot, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackContext,
    ContextTypes,
    ExtBot,
    TypeHandler,
)

from feedback_bot.telegram.builder.modules import ALL_MODULES
from feedback_bot.telegram.utils.modules_loader import load_modules

logging.getLogger('httpx').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


@dataclass
class WebhookUpdate:
    """Simple dataclass to wrap a custom update type"""

    user_id: int
    payload: str


class CustomContext(CallbackContext[ExtBot, dict, dict, dict]):
    """
    Custom CallbackContext class that makes `user_data` available for updates of type
    `WebhookUpdate`.
    """

    @classmethod
    def from_update(
        cls,
        update: object,
        application: 'Application',
    ) -> 'CustomContext':
        if isinstance(update, WebhookUpdate):
            return cls(application=application, user_id=update.user_id)
        return cast(CustomContext, super().from_update(update, application))


async def webhook_update(update: WebhookUpdate, context: CustomContext) -> None:
    """Handle custom updates."""
    chat_member = await context.bot.get_chat_member(chat_id=update.user_id, user_id=update.user_id)
    payloads = context.user_data.setdefault('payloads', [])
    payloads.append(update.payload)
    combined_payloads = '</code>\n• <code>'.join(payloads)
    text = (
        f'The user {chat_member.user.mention_html()} has sent a new payload. '
        f'So far they have sent the following payloads: \n\n• <code>{combined_payloads}</code>'
    )
    await context.bot.send_message(
        chat_id=settings.TELEGRAM_ADMIN_CHAT_ID, text=text, parse_mode=ParseMode.HTML
    )


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
            secret_token=settings.TELEGRAM_BUILDER_BOT_WEBHOOK_SECRET or None,
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


context_types = ContextTypes(context=CustomContext)
# Here we set updater to None because we want our custom webhook server to handle the updates
# and hence we don't need an Updater instance
ptb_application = (
    Application.builder()
    .token(settings.TELEGRAM_BUILDER_BOT_TOKEN)
    .updater(None)
    .context_types(context_types)
    .build()
)


ptb_application.add_handler(TypeHandler(type=WebhookUpdate, callback=webhook_update))


@asynccontextmanager
async def ptb_lifespan_manager() -> LifespanManager:
    logger.info('ASGI Lifespan: Starting up...')
    state = {'ptb_application': ptb_application}

    try:
        for module in load_modules(ALL_MODULES, 'feedback_bot.telegram.builder'):
            if hasattr(module, 'HANDLERS'):
                ptb_application.add_handlers(module.HANDLERS)
        async with ptb_application:
            await ptb_application.start()
            await ptb_application.bot.set_webhook(
                url=f'{settings.TELEGRAM_BUILDER_BOT_WEBHOOK_URL}/api/webhook/{settings.TELEGRAM_BUILDER_BOT_WEBHOOK_PATH}',
                secret_token=settings.TELEGRAM_BUILDER_BOT_WEBHOOK_SECRET or None,
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
