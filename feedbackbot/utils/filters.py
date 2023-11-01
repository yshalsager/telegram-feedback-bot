"""
Bot custom filters
"""
from telegram import Message
from telegram.ext.filters import MessageFilter

from feedbackbot import TG_BOT_ADMINS


class FilterBotAdmin(MessageFilter):
    def filter(self, message: Message) -> bool:  # noqa: A003
        return bool(message.from_user and message.from_user.id in TG_BOT_ADMINS)


class FilterTopicMessageReply(MessageFilter):
    def filter(self, message: Message) -> bool:  # noqa: A003
        return bool(
            message.is_topic_message
            and message.reply_to_message
            and (
                message.reply_to_message.forward_sender_name
                or (
                    message.reply_to_message.forward_from
                    and message.reply_to_message.forward_from.name
                )
            )
        )
