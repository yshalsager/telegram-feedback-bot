"""Bot stats module"""

from pyrogram import Client, filters
from pyrogram.types import Message

from src.bot.db.crud import get_chats_count, get_stats
from src.bot.db.session import session_scope
from src.bot.utils.filters import is_admin
from src.common.utils.telegram_handlers import tg_exceptions_handler


@Client.on_message(filters.command('stats') & is_admin)
@tg_exceptions_handler
async def stats(client: Client, message: Message) -> None:
    """
    Show Bot stats for admins.
    """
    with session_scope(client.me.id) as session:
        total_users_count: int = get_chats_count(session)
        messages_stats = get_stats(session)
        if messages_stats:
            incoming_count = messages_stats.incoming
            outgoing_count = messages_stats.outgoing
        else:
            incoming_count = outgoing_count = 0
    text_message = f"""📈 <b>إحصائيات البوت</b>

👥 <b>المستخدمون</b>
• {total_users_count} مستخدم للبوت

✍️ <b>الرسائل</b>
• {incoming_count} رسالة واردة
• {outgoing_count} رد على الرسائل
"""
    await message.reply_text(text_message, reply_to_message_id=message.reply_to_message_id)
