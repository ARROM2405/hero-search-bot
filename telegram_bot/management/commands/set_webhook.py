from django.core.management.base import BaseCommand, CommandError
import requests
import os

from dotenv import load_dotenv
from rest_framework import status


class Command(BaseCommand):
    help = "Sets the webhook for the telegram bot with the provided url."

    def add_arguments(self, parser):
        parser.add_argument(
            "--url",
            type=str,
            help="The webhook url.",
        )

    def handle(self, *args, **options):
        load_dotenv()
        url_tail = "/api/telegram_bot/user_message/"
        url: str = options["url"]
        if not url.endswith(url_tail):
            url += url_tail

        bot_token = os.getenv("BOT_TOKEN")

        self.stdout.write(self.style.NOTICE(f"Setting webhook to {url}"))

        response = requests.post(
            url=f"https://api.telegram.org/bot{bot_token}/setWebhook",
            data={"url": url},
        )
        if response.status_code != status.HTTP_200_OK or response.ok is not True:
            raise CommandError(
                f"setting webhook to {url} failed. Response: {response}."
            )
        self.stdout.write(self.style.SUCCESS(f"Webhook set successfully."))
