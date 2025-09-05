import logging

from django.conf import settings
from telegram import BotCommand
from telegram.ext import Application, CommandHandler

from feedback_bot.telegram.builder.modules import ALL_MODULES
from feedback_bot.telegram.utils.modules_loader import load_modules

logging.getLogger('httpx').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


# Here we set updater to None because we want our custom webhook server to handle the updates
# and hence we don't need an Updater instance
ptb_application = (
    Application.builder().token(settings.TELEGRAM_BUILDER_BOT_TOKEN).updater(None).build()
)


def load_builder_modules() -> list[BotCommand]:
    commands = []
    for module in load_modules(ALL_MODULES):
        if not hasattr(module, 'HANDLERS'):
            continue
        for handler in module.HANDLERS:
            ptb_application.add_handler(handler)
            if isinstance(handler, CommandHandler):
                for command in handler.commands:
                    commands.append(BotCommand(command, handler.callback.__doc__))
    return commands
