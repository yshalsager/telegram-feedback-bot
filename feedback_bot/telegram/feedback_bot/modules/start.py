from telegram import Update

from feedback_bot.models import Bot as BotConfig
from feedback_bot.telegram.feedback_bot.dispatcher import dispatcher


@dispatcher.command('start')
async def start(update: Update, **kwargs) -> None:
    """Display a welcome message."""
    bot_config: BotConfig = kwargs['bot_config']
    await update.message.reply_text(bot_config.start_message)
