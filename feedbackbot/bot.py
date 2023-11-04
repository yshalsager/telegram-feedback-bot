"""
Telegram Bot
"""
from feedbackbot import app


def main() -> None:
    """Run bot."""
    # Start the Bot
    # TODO Handle restart
    app.run()


if __name__ == "__main__":
    main()
