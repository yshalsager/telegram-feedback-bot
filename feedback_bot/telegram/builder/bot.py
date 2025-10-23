import logging
from functools import cache

from django.conf import settings
from telegram import BotCommand
from telegram.error import InvalidToken
from telegram.ext import Application, CommandHandler

from feedback_bot.telegram.builder.modules import ALL_MODULES
from feedback_bot.telegram.utils.errors import report_error
from feedback_bot.utils.modules_loader import load_modules

logging.getLogger('httpx').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


@cache
def get_ptb_application() -> Application:
    token = settings.TELEGRAM_BUILDER_BOT_TOKEN
    if not token:
        raise InvalidToken('TELEGRAM_BUILDER_BOT_TOKEN is not configured')
    # Here we set updater to None because we want our custom webhook server to handle the updates
    # and hence we don't need an Updater instance
    application = Application.builder().token(token).updater(None).build()
    application.add_error_handler(report_error)
    return application


def load_builder_modules() -> list[BotCommand]:
    commands = []
    ptb_application = get_ptb_application()
    for module in load_modules(ALL_MODULES):
        if not hasattr(module, 'HANDLERS'):
            continue
        for handler in module.HANDLERS:
            ptb_application.add_handler(handler)
            if isinstance(handler, CommandHandler):
                for command in handler.commands:
                    commands.append(BotCommand(command, handler.callback.__doc__))
    return commands
