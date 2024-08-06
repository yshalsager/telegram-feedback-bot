"""Bot Entry Point"""

from asyncio import run

import uvloop

from src.main import main

if __name__ == '__main__':
    uvloop.install()
    run(main())
