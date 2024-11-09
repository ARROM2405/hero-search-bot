from io import StringIO
from os import getenv
from unittest import mock

import dotenv
from django.core.management import CommandError, call_command
from django.test import TestCase
from precisely import assert_that, is_sequence
from rest_framework import status

dotenv.load_dotenv()


class TestSetWebhook(TestCase):
    @mock.patch("telegram_bot.management.commands.set_webhook.requests.post")
    def test_command_ok(self, mock_post):
        response_mock = mock.MagicMock()
        response_mock.ok = True
        response_mock.status_code = status.HTTP_200_OK
        mock_post.return_value = response_mock

        webhook_url = "http://localhost:8000/api/telegram_bot/user_message/"

        output = StringIO()
        call_command(
            "set_webhook",
            url=webhook_url,
            stdout=output,
        )

        bot_token = getenv("BOT_TOKEN")
        telegram_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"

        mock_post.assert_called_once_with(
            url=telegram_url,
            data={"url": webhook_url},
        )
        output.seek(0)
        assert_that(
            output.readlines(),
            is_sequence(
                f"Setting webhook to {webhook_url}\n",
                "Webhook set successfully.\n",
            ),
        )

    @mock.patch("telegram_bot.management.commands.set_webhook.requests.post")
    def test_command_url_tail_missing(self, mock_post):
        response_mock = mock.MagicMock()
        response_mock.ok = True
        response_mock.status_code = status.HTTP_200_OK
        mock_post.return_value = response_mock

        webhook_url = "http://localhost:8000"

        output = StringIO()
        call_command(
            "set_webhook",
            url=webhook_url,
            stdout=output,
        )

        bot_token = getenv("BOT_TOKEN")
        telegram_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"

        mock_post.assert_called_once_with(
            url=telegram_url,
            data={"url": f"{webhook_url}/api/telegram_bot/user_message/"},
        )
        output.seek(0)
        assert_that(
            output.readlines(),
            is_sequence(
                f"Setting webhook to {webhook_url}/api/telegram_bot/user_message/\n",
                "Webhook set successfully.\n",
            ),
        )

    @mock.patch("telegram_bot.management.commands.set_webhook.requests.post")
    def test_command_failed(self, mock_post):
        response_mock = mock.MagicMock()
        response_mock.ok = False
        response_mock.status_code = status.HTTP_400_BAD_REQUEST
        mock_post.return_value = response_mock

        webhook_url = "http://localhost:8000/api/telegram_bot/user_message/"

        output = StringIO()
        with self.assertRaises(CommandError):
            call_command(
                "set_webhook",
                url=webhook_url,
                stdout=output,
            )

        bot_token = getenv("BOT_TOKEN")
        telegram_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"

        mock_post.assert_called_once_with(
            url=telegram_url,
            data={"url": webhook_url},
        )
        output.seek(0)
        assert_that(
            output.readlines(),
            is_sequence(
                f"Setting webhook to {webhook_url}\n",
            ),
        )
