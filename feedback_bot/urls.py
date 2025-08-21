from django.conf import settings
from django.urls import path

from feedback_bot.views import (
    custom_updates,
    feedback_bot_webhook_handler,
    health_check,
    telegram_webhook_handler,
)

urlpatterns = [
    path(
        settings.TELEGRAM_BUILDER_BOT_WEBHOOK_NAME,
        telegram_webhook_handler,
        name='telegram_webhook',
    ),
    path('webhook/<uuid:bot_uuid>/', feedback_bot_webhook_handler, name='feedback_bot_webhook'),
    path('healthcheck', health_check, name='health_check'),
    path('submitpayload', custom_updates, name='submit_payload'),
]
