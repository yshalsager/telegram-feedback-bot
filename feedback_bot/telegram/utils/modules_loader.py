"""Bot modules dynamic loader"""

import logging
from importlib import import_module
from pathlib import Path
from types import ModuleType

logger = logging.getLogger(__name__)


def get_modules(modules_path: Path) -> filter:
    """Return all modules available in modules directory"""
    return filter(
        lambda x: x.name != '__init__.py' and x.suffix == '.py' and x.is_file(),
        modules_path.parent.glob('*.py'),
    )


def load_modules(modules: filter, directory: str) -> list[ModuleType]:
    """Load all modules in modules list"""
    loaded_modules = []
    for module in modules:
        module_name = f'{directory}.modules.{module.stem}'
        loaded_module = import_module(module_name)
        loaded_modules.append(loaded_module)
    logger.info(f'Loaded modules: {[module.__name__.split(".")[-1] for module in loaded_modules]}')
    return loaded_modules
