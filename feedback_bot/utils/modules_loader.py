"""Bot modules dynamic loader"""

import logging
from collections.abc import Iterator
from importlib import import_module
from pathlib import Path
from pkgutil import ModuleInfo, iter_modules
from types import ModuleType

from django.conf import settings

logger = logging.getLogger(__name__)


def get_modules(modules_path: Path) -> Iterator[ModuleInfo]:
    """Return all modules available in modules directory"""
    if not modules_path.is_absolute():
        modules_path = settings.BASE_DIR / modules_path

    relative_path = modules_path.relative_to(settings.BASE_DIR)
    prefix = f'{str(relative_path).replace("/", ".") + "."}'

    return iter_modules([modules_path], prefix=prefix)


def load_modules(modules: Iterator[ModuleInfo]) -> list[ModuleType]:
    """Load all modules in modules list"""
    loaded_modules = []
    for module_info in modules:
        module_name = module_info.name
        loaded_module = import_module(module_name)
        loaded_modules.append(loaded_module)
        logger.info(f'Loaded module: {module_name.split(".")[-1]}')
    logger.info(f'Total loaded modules: {len(loaded_modules)}')
    return loaded_modules
