import json
from pathlib import Path

from pyrogram import Client


async def handle_restart(parent_dir: Path, application: Client) -> None:
    # Restart handler
    restart_message_path: Path = parent_dir / 'restart.json'
    if restart_message_path.exists():
        restart_message = json.loads(restart_message_path.read_text())
        await application.edit_message_text(
            text='Restarted Successfully!',
            chat_id=restart_message['chat'],
            message_id=restart_message['message'],
        )
        restart_message_path.unlink()
