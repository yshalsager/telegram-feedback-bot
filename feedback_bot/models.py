import uuid

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
    username = models.CharField(max_length=255, null=True, blank=True)
    language_code = models.CharField(max_length=10, default='en')
    is_whitelisted = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f'@{self.username}' if self.username else str(self.telegram_id)


class Bot(TimestampedModel):
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
    name = models.CharField(max_length=255)
    username = models.CharField(max_length=255, unique=True)
    telegram_id = models.BigIntegerField(unique=True)

    # Encrypted token storage
    _token = models.CharField(max_length=255, db_column='token')

    @property
    def token(self) -> str:
        return decrypt_token(self._token)

    @token.setter
    def token(self, raw_token: str) -> None:
        self._token = encrypt_token(raw_token)

    # The chat where feedback messages are forwarded (can be a group or the owner's private chat)
    forward_chat_id = models.BigIntegerField()

    # Settings (migrated from JSON to plain fields for easier querying)
    start_message = models.TextField(default='Welcome! Send your feedback here.')
    feedback_received_message = models.TextField(default='Thank you for your feedback!')
    confirmations_on = models.BooleanField(
        default=True, help_text='Send confirmation messages to users.'
    )

    enabled = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f'@{self.username}'


class FeedbackChat(models.Model):
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
    owner_message_id = models.BigIntegerField(unique=True)

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

    class Meta:
        unique_together = ('bot', 'user_telegram_id')

    def __str__(self) -> str:
        return f'{self.user_telegram_id} banned from @{self.bot.username}'
