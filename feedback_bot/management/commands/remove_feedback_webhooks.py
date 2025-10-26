import asyncio

from django.core.management.base import BaseCommand

from feedback_bot.telegram.feedback_bot.bot import remove_bots_webhooks


class Command(BaseCommand):
    help = 'Remove webhooks for all feedback bots.'

    def handle(self, *args, **options) -> None:
        asyncio.run(remove_bots_webhooks())
        self.stdout.write(self.style.SUCCESS('Removed webhooks for all feedback bots'))
