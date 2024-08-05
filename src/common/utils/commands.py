import logging
from asyncio import create_subprocess_shell
from asyncio.subprocess import PIPE, STDOUT, Process

logger = logging.getLogger(__name__)


async def run_command(command: str) -> tuple[bool, str]:
    """
    Run a shell command asynchronously.
    :param command: Shell command to run.
    :return: True if return code is 0, False otherwise.
    """
    process: Process = await create_subprocess_shell(  # noqa: S604
        command,
        stdin=PIPE,
        stdout=PIPE,
        stderr=STDOUT,
        shell=True,
    )
    await process.wait()
    output: bytes = await process.stdout.read() if process.stdout else b''
    return process.returncode == 0, output.decode('utf-8')
