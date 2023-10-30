import json
from pathlib import Path

from telegram.ext import Application


async def handle_restart(parent_dir: Path, application: Application) -> None:
    # Restart handler
    restart_message_path: Path = parent_dir / "restart.json"
    if restart_message_path.exists():
        restart_message = json.loads(restart_message_path.read_text())
        await application.bot.edit_message_text(
            "`Restarted Successfully!`",
            restart_message["chat"],
            restart_message["message"],
        )
        restart_message_path.unlink()
