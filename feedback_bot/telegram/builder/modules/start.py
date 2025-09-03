from django.conf import settings
from django.utils.translation import gettext_lazy as _
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import CallbackContext, CommandHandler

from feedback_bot.telegram.builder.crud import create_user
from feedback_bot.telegram.builder.filters import whitelisted_only


@whitelisted_only
async def start(update: Update, context: CallbackContext) -> None:
    """Display a message with instructions on how to use this bot."""
    assert update.message.from_user is not None
    await create_user(update.message.from_user.to_dict())
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
            [
                InlineKeyboardButton(
                    'Open Mini App',
                    web_app=WebAppInfo(url=f'{settings.TELEGRAM_BUILDER_BOT_WEBHOOK_URL}/'),
                )
            ],
        ]
    )

    await update.message.reply_text(str(message), reply_markup=keyboard)


HANDLERS = [
    CommandHandler('start', start),
]
