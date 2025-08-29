import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import cast

from django.conf import settings
from django_asgi_lifespan.types import LifespanManager
from telegram import Update
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
            # logger.info(
            #     f'Webhook for main bot set to {settings.TELEGRAM_BUILDER_BOT_WEBHOOK_URL}/{settings.TELEGRAM_BUILDER_BOT_WEBHOOK_PATH}'
            # )
            logger.info('ASGI Lifespan: PTB application started and webhook is set.')

            yield state
    finally:
        await state['ptb_application'].bot.delete_webhook()
        await state['ptb_application'].stop()
        await state['ptb_application'].shutdown()
        logger.info('ASGI Lifespan: PTB application stopped.')
