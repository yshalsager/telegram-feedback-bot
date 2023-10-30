""" Bot restart module"""
import json
from os import execl
from pathlib import Path
from sys import executable

from telegram import Update
from telegram.ext import ContextTypes

from feedbackbot import PARENT_DIR
from feedbackbot.utils.filters import FilterBotAdmin
from feedbackbot.utils.telegram_handlers import command_handler


@command_handler("restart", FilterBotAdmin())
async def restart(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """restarts the bot."""
    assert update.effective_message is not None
    restart_message = await update.effective_message.reply_text(
        "`Restarting, please wait...`",
    )
    chat_info = {"chat": restart_message.chat_id, "message": restart_message.message_id}
    Path(f"{PARENT_DIR}/restart.json").write_text(json.dumps(chat_info))
    execl(executable, executable, "-m", __package__.split(".")[0])  # noqa: S606
