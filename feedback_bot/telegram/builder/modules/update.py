"""Bot update module"""

from asyncio import create_subprocess_exec
from asyncio.subprocess import PIPE
from html import escape

from django.conf import settings
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from feedback_bot.telegram.builder.filters import is_admin
from feedback_bot.telegram.builder.modules.restart import restart


async def _run_command(*args: str) -> tuple[int, str, str]:
    process = await create_subprocess_exec(
        *args,
        stdout=PIPE,
        stderr=PIPE,
        cwd=settings.BASE_DIR,
    )
    stdout, stderr = await process.communicate()
    return process.returncode, stdout.decode(errors='replace'), stderr.decode(errors='replace')


async def update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Update the bot code and restart."""
    message = update.message
    if message is None:
        return

    update_message = await message.reply_text(
        'Updating, please wait...',
        reply_to_message_id=message.message_id,
    )

    try:
        branch_rc, branch_stdout, branch_stderr = await _run_command(
            'git',
            'rev-parse',
            '--abbrev-ref',
            'HEAD',
        )
        if branch_rc != 0:
            await update_message.edit_text(
                f'Git update failed. Error: <pre>{escape(branch_stderr)}</pre>'
            )
            return
        branch = branch_stdout.strip() or 'main'
        if branch == 'HEAD':
            branch = 'main'

        fetch_rc, _, fetch_stderr = await _run_command('git', 'fetch', 'origin', branch)
        if fetch_rc != 0:
            await update_message.edit_text(
                f'Git fetch failed. Error: <pre>{escape(fetch_stderr)}</pre>'
            )
            return

        reset_rc, reset_stdout, reset_stderr = await _run_command(
            'git',
            'reset',
            '--hard',
            f'origin/{branch}',
        )
        if reset_rc != 0:
            await update_message.edit_text(
                f'Git reset failed. Error: <pre>{escape(reset_stderr)}</pre>'
            )
            return

        reset_output = reset_stdout.strip()
        git_success_message = 'Git update successful.'
        if reset_output:
            git_success_message = f'{git_success_message}\n<pre>{escape(reset_output)}</pre>'
        await update_message.edit_text(f'{git_success_message}\nSyncing dependencies...')

        sync_rc, _, sync_stderr = await _run_command('uv', 'sync')
        if sync_rc != 0:
            await update_message.edit_text(
                f'Dependency sync failed. Error: <pre>{escape(sync_stderr)}</pre>'
            )
            return

        await update_message.edit_text('Update was successful. Restarting...')
    except Exception as exc:  # noqa: BLE001
        await update_message.edit_text(f'Update failed. Error: <pre>{escape(str(exc))}</pre>')
        return

    await restart(update, context)


HANDLERS = [CommandHandler('update', update, is_admin)]
