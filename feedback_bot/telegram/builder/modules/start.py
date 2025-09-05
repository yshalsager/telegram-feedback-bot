from django.conf import settings
from django.utils.translation import gettext_lazy as _
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import CallbackContext, CommandHandler

from feedback_bot.telegram.builder.filters import whitelisted_only
from feedback_bot.telegram.crud import create_user


@whitelisted_only
async def start(update: Update, context: CallbackContext) -> None:
    """Start the bot and show the main menu."""
    assert update.message.from_user is not None
    await create_user(update.message.from_user.to_dict())
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
