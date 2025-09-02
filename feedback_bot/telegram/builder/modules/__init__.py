"""Modules loader"""

from collections.abc import Iterator
from pathlib import Path
from pkgutil import ModuleInfo

from feedback_bot.telegram.utils.modules_loader import get_modules

ALL_MODULES: Iterator[ModuleInfo] = get_modules(Path(__file__).parent)
