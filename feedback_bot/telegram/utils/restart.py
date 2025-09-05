import orjson
from django.conf import settings
from django.utils.translation import gettext as _
from telegram.ext import Application


async def handle_restart(application: Application) -> None:
    restart_message_path = settings.BASE_DIR / 'restart.json'
    if not restart_message_path.exists():
        return
    restart_message = orjson.loads(restart_message_path.read_text())
    await application.bot.edit_message_text(
        text=str(_('restarted_successfully')),
        chat_id=restart_message['chat'],
        message_id=restart_message['message'],
    )
    restart_message_path.unlink()
