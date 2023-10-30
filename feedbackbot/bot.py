"""
Telegram Bot
"""
from feedbackbot import application
from feedbackbot.modules import ALL_MODULES
from feedbackbot.utils.modules_loader import load_modules


def main() -> None:
    """Run bot."""
    # Load all modules in modules list
    load_modules(ALL_MODULES, __package__)
    # Start the Bot
    application.run_polling()


if __name__ == "__main__":
    main()
