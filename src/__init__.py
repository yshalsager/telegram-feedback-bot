"""Bot initialization"""

import logging
from os import getenv
from pathlib import Path

from pyrogram import Client

# paths
WORK_DIR = Path(__package__)
PARENT_DIR = WORK_DIR.parent
DB_PATH = PARENT_DIR / 'feedback_bot.db'
DATA_DIR = Path(PARENT_DIR / 'data')
DATA_DIR.mkdir(parents=True, exist_ok=True)

# bot config
IS_DEBUG: bool = getenv('DEBUG', '').lower() in {'true', '1'}
BOT_TOKEN = getenv('BOT_TOKEN', '')
API_ID = getenv('API_ID')
API_HASH = getenv('API_HASH')
BOT_ADMINS = [
    int(admin_str.strip()) for admin_str in getenv('BOT_ADMINS', '').split(',') if admin_str
] or []
TELEGRAM_CHAT_ID = getenv('CHAT_ID', '')
LOG_TOPIC_ID = getenv('LOG_TOPIC_ID', '')
NEW_BOT_ADMIN_APPROVAL = getenv('NEW_BOT_ADMIN_APPROVAL', '').lower() in {'true', '1'}

# encryption key
ENCRYPTION_KEY = getenv('ENCRYPTION_KEY', '')

# Logging
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
LOG_PATH = PARENT_DIR
if IS_DEBUG:
    from rich.logging import Console, RichHandler

    logging.basicConfig(
        format='[%(module)s.%(funcName)s:%(lineno)d]: %(message)s',  # rich adds time and level
        level=logging.INFO,
        handlers=[RichHandler(rich_tracebacks=True, console=Console(width=150))],
        datefmt=LOG_DATE_FORMAT,
    )
else:
    logging.basicConfig(
        format='%(asctime)s [%(levelname)s] %(name)s [%(module)s.%(funcName)s:%(lineno)d]: %(message)s',
        level=logging.INFO,
        datefmt=LOG_DATE_FORMAT,
    )

BOTS: dict[int, Client] = {}
