from django.conf import settings
from django.utils.translation import gettext_lazy as _
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import CallbackContext, CommandHandler

from feedback_bot.crud import create_user
from feedback_bot.telegram.builder.filters import whitelisted_only


@whitelisted_only
async def start(update: Update, context: CallbackContext) -> None:
    """Start the bot and show the main menu."""
    assert update.message.from_user is not None
    await create_user(update.message.from_user.to_dict())
    message = _('welcome')
    keyboard = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton(
            str(_('open_mini_app')),
            web_app=WebAppInfo(url=f'{settings.TELEGRAM_BUILDER_BOT_WEBHOOK_URL.rstrip("/")}/app/'),
        )
    )

    await update.message.reply_text(str(message), reply_markup=keyboard)


HANDLERS = [
    CommandHandler('start', start),
]
