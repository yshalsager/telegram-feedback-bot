import logging
from asyncio import sleep

from pyrogram.errors import FloodWait, RPCError
from pyrogram.types import Message

SLEEP_AFTER_SEND = 0.035  # Limit is ~30 messages/second; core.telegram.org/bots/faq

logger = logging.getLogger(__name__)


async def broadcast_messages(chats: list[int], message_to_send: Message) -> str:
    failed_to_send = 0
    sent_successfully = 0
    for chat_id in chats:
        try:
            await message_to_send.copy(chat_id=chat_id)
            sent_successfully += 1
            await sleep(SLEEP_AFTER_SEND)
        except FloodWait as err:
            await sleep(err.value + 1)
            await message_to_send.copy(chat_id=chat_id)
            sent_successfully += 1
            await sleep(SLEEP_AFTER_SEND)
        except RPCError as err:
            failed_to_send += 1
            logger.warning(f'فشل إرسال الرسالة إلى {chat_id}:\n{err}')
    broadcast_status_message: str = (
        f'اكتمل النشر! أرسلت الرسالة إلى {sent_successfully} مستخدم ومجموعة\n'
    )
    if failed_to_send:
        broadcast_status_message += (
            f' فشل الإرسال إلى {failed_to_send}'
            f'مستخدمين/مجموعات، غالبا بسبب أن البوت طرد أو أوقف.'
        )
    return broadcast_status_message


def get_bot_id(bot_token: str) -> int:
    return int(bot_token.split(':')[0])
