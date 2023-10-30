"""Bot modules dynamic loader"""
import logging
from importlib import import_module
from pathlib import Path

logger = logging.getLogger(__name__)


def get_modules(modules_path: Path) -> filter:
    """Return all modules available in modules directory"""
    return filter(
        lambda x: x.name != "__init__.py" and x.suffix == ".py" and x.is_file(),
        modules_path.parent.glob("*.py"),
    )


def load_modules(modules: filter, directory: str) -> None:
    """Load all modules in modules list"""
    loaded_modules = []
    for module in modules:
        module_name = f"{directory}.modules.{module.stem}"
        import_module(module_name)
        loaded_modules.append(module.stem)
    logger.info(f"Loaded modules: {loaded_modules!s}")
