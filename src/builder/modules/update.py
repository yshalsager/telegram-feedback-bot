"""Bot update module"""

from asyncio import create_subprocess_shell
from asyncio.subprocess import PIPE

from pyrogram import Client, filters
from pyrogram.types import Message

from src import BOT_ADMINS, PARENT_DIR
from src.builder.modules.restart import restart
from src.common.utils.filters import is_admin


@Client.on_message(filters.command('update') & is_admin(BOT_ADMINS))
async def update(_: Client, message: Message) -> None:
    """Update and restart the bot."""
    update_message = await message.reply_text(
        'Updating, please wait...',
        reply_to_message_id=message.reply_to_message_id,
    )

    try:
        git_update_command = 'git fetch origin master && git reset --hard origin/master'
        git_process = await create_subprocess_shell(
            git_update_command,
            stdout=PIPE,
            stderr=PIPE,
            cwd=PARENT_DIR,
        )
        git_stdout, git_stderr = await git_process.communicate()
        if git_process.returncode != 0:
            await update_message.edit_text(
                f'Git update failed. Error: <pre>{git_stderr.decode()}</pre>'
            )
            return
        await update_message.edit_text(
            f'Git update successful. Updating requirements...' f'\n<pre>{git_stdout.decode()}</pre>'
        )

        req_process = await create_subprocess_shell(
            'pip install -r requirements.txt',
            stdout=PIPE,
            stderr=PIPE,
            cwd=PARENT_DIR,
        )
        __, req_stderr = await req_process.communicate()

        if req_process.returncode == 0:
            await update_message.edit_text('Update was successful. Restarting...</pre>')
        else:
            await update_message.edit_text(
                f'Requirements update failed. Error: <pre>{req_stderr.decode()}</pre>'
            )
            return
    except Exception as e:  # noqa: BLE001
        await update_message.edit_text(f'Update failed. Error: <pre>{e!s}</pre>')
        return

    await restart(_, update_message)
