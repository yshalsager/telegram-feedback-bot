"""
Telegram Bot
"""

import logging

from pyrogram import Client, idle
from pyrogram.enums import ParseMode
from pyrogram.errors import AccessTokenInvalid

from src import API_HASH, API_ID, BOT_TOKEN, BOTS, DATA_DIR, PARENT_DIR
from src.builder.db.crud import get_bots_tokens, remove_bot
from src.common.utils.restart import handle_restart
from src.common.utils.telegram import get_bot_id

package_name = __package__.split('.')[0]


async def main() -> None:
    """Run bots."""
    main_bot_id = get_bot_id(BOT_TOKEN)
    app = Client(
        'feedbackbot',
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
        plugins={'root': f'{package_name}.builder.modules'},
        parse_mode=ParseMode.HTML,
        workdir=DATA_DIR,
    )
    await app.start()
    BOTS.update({main_bot_id: app})
    await handle_restart(PARENT_DIR, app)

    for bot_token, bot_owner, bot_username in get_bots_tokens():
        bot_id = get_bot_id(bot_token)
        bot = Client(
            str(bot_id),
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=bot_token,
            plugins={'root': f'{package_name}.bot.modules'},
            parse_mode=ParseMode.HTML,
            workdir=DATA_DIR,
        )
        BOTS.update({bot_id: bot})
        try:
            await bot.start()
        except AccessTokenInvalid as err:
            logging.warning(f'Incorrect token for bot {bot_id}: {err}')
            remove_bot(bot_id, bot_owner)
            for i in DATA_DIR.glob(f'{bot_id}.*'):
                i.unlink(missing_ok=True)
            await app.send_message(
                bot_owner,
                f'Bot @{bot_username} was removed. Reason: incorrect token.',
            )
            BOTS.pop(bot_id)
            continue

    await idle()
    for bot in BOTS.values():
        await bot.stop()
