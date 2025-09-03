import logging

from django.apps import AppConfig
from django_asgi_lifespan.register import register_lifespan_manager

from feedback_bot.telegram.init import ptb_lifespan_manager

logger = logging.getLogger(__name__)


class FeedbackBotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'feedback_bot'

    def ready(self):
        register_lifespan_manager(context_manager=ptb_lifespan_manager)
