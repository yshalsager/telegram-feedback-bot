""" Bot initialization """
import logging
from functools import partial
from os import getenv
from pathlib import Path
from warnings import filterwarnings

from telegram.constants import ParseMode
from telegram.ext import (
    AIORateLimiter,
    Application,
    ApplicationBuilder,
    Defaults,
    PicklePersistence,
)
from telegram.warnings import PTBUserWarning

from feedbackbot.utils.restart import handle_restart

# paths
WORK_DIR = Path(__package__)
PARENT_DIR = WORK_DIR.parent
DB_PATH = PARENT_DIR / "feedback_bot.db"

# bot config
IS_DEBUG: bool = getenv("DEBUG", "").lower() in ("true", "1")
BOT_TOKEN = getenv("TELEGRAM_BOT_TOKEN")
TG_BOT_ADMINS = [
    int(admin_str.strip())
    for admin_str in getenv("TELEGRAM_BOT_ADMINS", "").split(",")
    if admin_str
] or []
TELEGRAM_CHAT_ID = getenv("TELEGRAM_CHAT_ID", "")
TELEGRAM_LOG_TOPIC_ID = getenv("TELEGRAM_LOG_TOPIC_ID", "")
SLEEP_AFTER_SEND = 0.035  # Limit is ~30 messages/second; core.telegram.org/bots/faq

# Logging
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_PATH = PARENT_DIR
if IS_DEBUG:
    from rich.logging import Console, RichHandler

    logging.basicConfig(
        format="[%(module)s.%(funcName)s:%(lineno)d]: %(message)s",  # rich adds time and level
        level=logging.INFO,
        handlers=[RichHandler(rich_tracebacks=True, console=Console(width=150))],
        datefmt=LOG_DATE_FORMAT,
    )
else:
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(name)s [%(module)s.%(funcName)s:%(lineno)d]: %(message)s",
        level=logging.INFO,
        datefmt=LOG_DATE_FORMAT,
    )

# bot
if BOT_TOKEN:
    persistence = PicklePersistence(filepath=f"{PARENT_DIR}/bot.pickle")
    defaults = Defaults(parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
    application: Application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .defaults(defaults)
        .persistence(persistence)
        .post_init(partial(handle_restart, PARENT_DIR))
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .pool_timeout(30)
        .get_updates_read_timeout(30)
        .connection_pool_size(512)
        .http_version("1.1")
        .get_updates_http_version("1.1")
        .rate_limiter(AIORateLimiter(max_retries=5))
        .build()
    )

logging.getLogger("httpx").setLevel(logging.WARNING)
filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)
