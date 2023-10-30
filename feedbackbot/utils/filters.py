"""
Bot custom filters
"""
from telegram import Message
from telegram.ext.filters import MessageFilter

from feedbackbot import TG_BOT_ADMINS


class FilterBotAdmin(MessageFilter):
    def filter(self, message: Message) -> bool:  # noqa: A003
        return bool(message.from_user and message.from_user.id in TG_BOT_ADMINS)
