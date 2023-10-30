"""Modules loader"""
from pathlib import Path

from feedbackbot.utils.modules_loader import get_modules

ALL_MODULES: filter = get_modules(Path(__file__))
