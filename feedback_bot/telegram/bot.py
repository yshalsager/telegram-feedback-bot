import html
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass

from django.conf import settings
from django.utils.translation import activate, get_language_info
from django.utils.translation import gettext_lazy as _
from django_asgi_lifespan.types import LifespanManager
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackContext,
    CommandHandler,
    ContextTypes,
    ExtBot,
    TypeHandler,
)

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
        return super().from_update(update, application)


async def start(update: Update, context: CustomContext) -> None:
    """Display a message with instructions on how to use this bot."""
    # payload_url = html.escape(
    #     f'{settings.TELEGRAM_BUILDER_BOT_WEBHOOK_URL}/submitpayload?user_id=<your user id>&payload=<payload>'
    # )
    # text = (
    #     f'To check if the bot is still running, call <code>{settings.TELEGRAM_BUILDER_BOT_WEBHOOK_URL}/healthcheck</code>.\n\n'
    #     f'To post a custom update, call <code>{payload_url}</code>.'
    # )
    # logger.info(f'Language: {get_language_info(update.message.from_user.language_code)}')
    # activate(update.message.from_user.language_code)
    # activate('ar')
    message = _('welcome')
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(f'{_("add_bot")}', callback_data='add_bot')],
            [InlineKeyboardButton(f'{_("manage_bots")}', callback_data='manage_bots')],
            [InlineKeyboardButton(f'{_("manage_settings")}', callback_data='manage_settings')],
        ]
    )

    await update.message.reply_text(str(message), reply_markup=keyboard)


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

ptb_application.add_handler(CommandHandler('start', start))
ptb_application.add_handler(TypeHandler(type=WebhookUpdate, callback=webhook_update))


@asynccontextmanager
async def ptb_lifespan_manager() -> LifespanManager:
    logger.info('ASGI Lifespan: Starting up...')
    state = {'ptb_application': ptb_application}

    try:
        async with ptb_application:
            await ptb_application.start()
            await ptb_application.bot.set_webhook(
                url=f'{settings.TELEGRAM_BUILDER_BOT_WEBHOOK_URL}/{settings.TELEGRAM_BUILDER_BOT_WEBHOOK_NAME}',
                secret_token=settings.TELEGRAM_BUILDER_BOT_WEBHOOK_SECRET or None,
                allowed_updates=Update.ALL_TYPES,
            )
            # logger.info(
            #     f'Webhook for main bot set to {settings.TELEGRAM_BUILDER_BOT_WEBHOOK_URL}/{settings.TELEGRAM_BUILDER_BOT_WEBHOOK_NAME}'
            # )
            logger.info('ASGI Lifespan: PTB application started and webhook is set.')

            yield state
    finally:
        await state['ptb_application'].stop()
        logger.info('ASGI Lifespan: PTB application stopped.')
