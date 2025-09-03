from telegram import Update
from telegram.ext import CommandHandler, ContextTypes


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display a welcome message."""
    await update.message.reply_text(context.bot_data['bot_config'].start_message)


HANDLERS = [
    CommandHandler('start', start),
]
