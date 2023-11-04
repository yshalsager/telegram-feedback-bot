""" Bot initialization """
import logging
from os import getenv
from pathlib import Path

from pyrogram import Client
from pyrogram.enums import ParseMode

# paths
WORK_DIR = Path(__package__)
PARENT_DIR = WORK_DIR.parent
DB_PATH = PARENT_DIR / "feedback_bot.db"

# bot config
IS_DEBUG: bool = getenv("DEBUG", "").lower() in ("true", "1")
BOT_TOKEN = getenv("TELEGRAM_BOT_TOKEN")
API_ID = getenv("TELEGRAM_API_ID")
API_HASH = getenv("TELEGRAM_API_HASH")
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
    app = Client("feedbackbot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
    app.set_parse_mode(ParseMode.HTML)
