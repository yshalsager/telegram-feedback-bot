import uuid
from typing import ClassVar

from django.conf import settings
from django.db import models

from feedback_bot.telegram.utils.cryptography import decrypt_token, encrypt_token


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class User(TimestampedModel):
    """
    Represents a user of the main builder bot.
    """

    telegram_id = models.BigIntegerField(unique=True, primary_key=True)
    username = models.CharField(max_length=32, null=True, blank=True)
    language_code = models.CharField(max_length=10, default='en')
    is_whitelisted = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f'@{self.username}' if self.username else str(self.telegram_id)


class Bot(TimestampedModel):
    class CommunicationMode(models.TextChoices):
        STANDARD = 'standard', 'standard'
        PRIVATE = 'private', 'private'
        ANONYMOUS = 'anonymous', 'anonymous'

    """
    The central model representing each feedback bot created by a User.
    This merges concepts from telegram-feedback-bot's Bot model and olgram's Bot model.
    The webhook URL will be constructed using the 'uuid' field.
    """

    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text='UUID for webhook URL to avoid exposing tokens.',
    )
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bots')
    name = models.CharField(max_length=64)
    username = models.CharField(max_length=32, unique=True)
    telegram_id = models.BigIntegerField(unique=True)

    # Encrypted token storage
    _token = models.CharField(unique=True, max_length=255, db_column='token')

    @property
    def token(self) -> str:
        return decrypt_token(self._token)

    @token.setter
    def token(self, raw_token: str) -> None:
        self._token = encrypt_token(raw_token)

    # The chat where feedback messages are forwarded (can be a group or the owner's private chat)
    forward_chat_id = models.BigIntegerField(blank=True, null=True)

    # Settings (migrated from JSON to plain fields for easier querying)
    start_message = models.TextField(default='Welcome! Send your feedback here.', max_length=4096)
    feedback_received_message = models.TextField(
        default='Thank you for your feedback!', max_length=4096
    )

    enabled = models.BooleanField(default=not settings.TELEGRAM_NEW_BOT_ADMIN_APPROVAL)
    allow_photo_messages = models.BooleanField(default=True)
    allow_video_messages = models.BooleanField(default=True)
    allow_voice_messages = models.BooleanField(default=True)
    allow_document_messages = models.BooleanField(default=True)
    allow_sticker_messages = models.BooleanField(default=True)
    antiflood_enabled = models.BooleanField(default=False)
    antiflood_seconds = models.PositiveIntegerField(default=60)
    communication_mode = models.CharField(
        max_length=16,
        choices=CommunicationMode.choices,
        default=CommunicationMode.STANDARD,
    )

    def __str__(self) -> str:
        return f'@{self.username}'


class FeedbackChat(TimestampedModel):
    """
    Represents a unique user who has started interacting with a specific feedback Bot.
    This replaces the 'Chat' and 'Topic' models from telegram-feedback-bot's bot-specific DBs.
    """

    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, related_name='feedback_chats')
    user_telegram_id = models.BigIntegerField()
    username = models.CharField(max_length=255, null=True, blank=True)
    topic_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text='The ID of the forum topic for this user in the forward_chat_id group.',
    )
    last_feedback_at = models.DateTimeField(null=True, blank=True)
    last_warning_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('bot', 'user_telegram_id')

    def __str__(self) -> str:
        return f'Chat with {self.user_telegram_id} for @{self.bot.username}'


class MessageMapping(models.Model):
    """
    Maps a message from a user to the forwarded message in the owner's chat.
    This is essential for routing replies correctly and replaces the 'Mapping' model.
    """

    bot = models.ForeignKey(Bot, on_delete=models.CASCADE)
    user_chat = models.ForeignKey(FeedbackChat, on_delete=models.CASCADE)

    # Message ID in the user's private chat with the bot
    user_message_id = models.BigIntegerField()
    # Message ID of the forwarded message in the owner's chat/group
    owner_message_id = models.BigIntegerField()

    class Meta:
        # Each message from the user can only be mapped once
        unique_together = ('bot', 'user_message_id')


class BotStats(models.Model):
    """
    Stores statistics for each bot. A simpler replacement for the 'Stat' model.
    """

    bot = models.OneToOneField(
        Bot, on_delete=models.CASCADE, primary_key=True, related_name='stats'
    )
    incoming_messages = models.PositiveIntegerField(default=0)
    outgoing_messages = models.PositiveIntegerField(default=0)

    def __str__(self) -> str:
        return f'Stats for @{self.bot.username}'


class BannedUser(TimestampedModel):
    """
    A user banned from a specific bot. Inspired by olgram.
    """

    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, related_name='banned_users')
    user_telegram_id = models.BigIntegerField()
    reason = models.TextField(blank=True, default='')

    class Meta:
        unique_together = ('bot', 'user_telegram_id')

    def __str__(self) -> str:
        return f'{self.user_telegram_id} banned from @{self.bot.username}'


class BroadcastMessage(models.Model):
    """Stores outbound broadcast copies per target chat."""

    bot = models.ForeignKey(
        Bot,
        on_delete=models.CASCADE,
        related_name='broadcast_messages',
        null=True,
        blank=True,
    )
    chat_id = models.BigIntegerField()
    message_id = models.BigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering: ClassVar[list[str]] = ['-created_at']
        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=['bot', 'chat_id'], name='broadcast_bot_chat_idx')
        ]

    def __str__(self) -> str:
        target = self.bot.username if self.bot else 'builder'
        return f'broadcast to {target} #{self.chat_id}'
