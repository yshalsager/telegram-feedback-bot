import logging
from pathlib import Path

from telegram.ext import Application

from feedback_bot.models import Bot as BotConfig
from feedback_bot.telegram.utils.modules_loader import get_modules, load_modules

logger = logging.getLogger(__name__)


def build_feedback_bot_application(bot_config: BotConfig) -> Application:
    """
    Builds and configures a lightweight, request-scoped PTB Application
    for a feedback bot.
    """
    application = (
        Application.builder()
        .updater(None)
        .job_queue(None)
        .rate_limiter(None)
        .concurrent_updates(1)
        .token(bot_config.token)
        .build()
    )

    application.bot_data['bot_config'] = bot_config

    for module in load_modules(get_modules(Path(__file__).parent / 'modules')):
        if hasattr(module, 'HANDLERS'):
            application.add_handlers(module.HANDLERS)

    return application
