import logging

from telegram import Bot, Update

logger = logging.getLogger(__name__)


class HandlerDispatcher:
    def __init__(self):
        # Store handlers in categorized buckets
        self._command_handlers = {}  # Maps command name to callback
        self._message_handlers = []  # List of (filter, callback) for general messages
        self._reply_handlers = []  # List of (filter, callback) for replies

    # --- Registration Methods (used by decorators) ---
    def command(self, name: str):
        """Decorator to register a command handler."""

        def decorator(callback_func):
            logger.info(f'Registering command: /{name}')
            self._command_handlers[name] = callback_func
            return callback_func

        return decorator

    def message(self, filter_obj):
        """Decorator to register a general message handler."""

        def decorator(callback_func):
            logger.info(f'Registering message handler: {callback_func.__module__}')
            self._message_handlers.append((filter_obj, callback_func))
            return callback_func

        return decorator

    def reply(self, filter_obj):
        """Decorator to register a reply handler."""

        def decorator(callback_func):
            logger.info(f'Registering reply handler: {callback_func.__module__}')
            self._reply_handlers.append((filter_obj, callback_func))
            return callback_func

        return decorator

    # --- Dispatch Methods (used by the main router) ---
    async def dispatch_command(self, name: str, update: Update, **kwargs):
        """Finds and executes the correct command callback."""
        callback_func = self._command_handlers.get(name)
        if callback_func:
            await callback_func(update, **kwargs)
            return True
        return False

    async def dispatch_message(self, update: Update, bot_config: Bot):
        """Finds and executes the first matching message handler."""
        for filter_obj, callback_func in self._message_handlers:
            if filter_obj.check_update(update):
                await callback_func(update, bot_config)
                return True
        return False

    async def dispatch_reply(self, update: Update, bot_config: Bot):
        """Finds and executes the first matching reply handler."""
        for filter_obj, callback_func in self._reply_handlers:
            if filter_obj.check_update(update):
                await callback_func(update, bot_config)
                return True
        return False


dispatcher = HandlerDispatcher()
