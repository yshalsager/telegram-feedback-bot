import logging
from pathlib import Path

from telegram import Bot, Update

from feedback_bot.models import Bot as BotConfig
from feedback_bot.telegram.feedback_bot.dispatcher import dispatcher
from feedback_bot.telegram.utils.modules_loader import get_modules, load_modules

logger = logging.getLogger(__name__)


load_modules(get_modules(Path(__file__).parent / 'modules'))
logger.info('Handler modules loaded and registered')


async def process_update(update: Update, bot: Bot, bot_config: BotConfig) -> None:
    """
    Processes an update by categorizing it and dispatching it to the correct handler.
    """
    message = update.effective_message
    if not message:
        logger.info(f'Ignoring non-message update for @{bot_config.username}')
        return

    was_handled = False
    try:
        # 1. Pre-resolve: Is it a command? (Most specific)
        if message.text and message.text.startswith('/'):
            command_name = message.text.split(' ')[0].lstrip('/')
            was_handled = await dispatcher.dispatch_command(
                command_name, update, bot_config=bot_config
            )

        # 2. Pre-resolve: Is it a reply?
        elif message.reply_to_message:
            was_handled = await dispatcher.dispatch_reply(update, bot)

        # 3. Pre-resolve: It must be a general message.
        else:
            was_handled = await dispatcher.dispatch_message(update, bot)

    except Exception:
        logger.exception(f'Dispatcher failed for @{bot_config.username}')
        return  # Stop processing on failure

    if not was_handled:
        logger.warning(
            f'No handler was found for update on @{bot_config.username}: {update.to_json()}'
        )
