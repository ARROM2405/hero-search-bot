import json

from precisely import assert_that, is_mapping
from rest_framework import status
from rest_framework.reverse import reverse
from unittest import mock

from telegram_bot.constants import BASE_URL
from telegram_bot.test.base import TelegramBotRequestsTestBase


class TestTelegramBotApiViewSet(TelegramBotRequestsTestBase):
    def setUp(self):
        super().setUp()
        self.url = reverse("telegram_bot:telegram_bot-user-message")

    # Private chat

    @mock.patch("telegram_bot.message_handling_services.requests.post")
    def test_start_command_in_the_private_chat(self, mock_post):
        self.command_as_message_in_private_chat_request_payload["message"][
            "text"
        ] = "/start"
        chat_id_from_the_command = (
            self.command_as_message_in_private_chat_request_payload["message"]["chat"][
                "id"
            ]
        )
        _message_id_from_the_command = (
            self.command_as_message_in_private_chat_request_payload["message"][
                "message_id"
            ]
        )
        response = self.client.post(
            self.url,
            data=json.dumps(self.command_as_message_in_private_chat_request_payload),
            content_type="application/json",
        )
        assert response.status_code == status.HTTP_200_OK

        # TODO: if command is received as a message, remove markup call is not needed
        assert mock_post.call_count == 2
        assert_that(
            mock_post.call_args_list[0].kwargs,
            is_mapping(
                {
                    "url": BASE_URL + "editMessageReplyMarkup",
                    "json": is_mapping(
                        {
                            "chat_id": chat_id_from_the_command,
                            "message_id": None,
                            "reply_markup": is_mapping({"inline_keyboard": []}),
                        }
                    ),
                }
            ),
        )  # remove_reply_markup

        assert_that(
            mock_post.call_args_list[1].kwargs,
            is_mapping(
                {
                    "url": BASE_URL + "sendMessage",
                    "data": is_mapping(
                        {
                            "chat_id": chat_id_from_the_command,
                            "text": """
Привіт, я бот для передачі інформації по пошуку героя ЗСУ.
Я буду просити тебе по черзі відправляти мені дані.
В кінці буде можливість все перепровірити і, якщо необхідно,
відмінити прийняття надісланих даних і все відправити з самого початку.""",
                            "reply_markup": json.dumps(
                                {
                                    "inline_keyboard": [
                                        [
                                            {
                                                "text": "Зрозуміло, починаємо",
                                                "callback_data": "/instructions_confirmed",
                                            }
                                        ]
                                    ]
                                }
                            ),
                        }
                    ),
                }
            ),
        )  # remove_reply_markup

    def test_bot_kicked_from_the_private_chat(self):
        raise AssertionError

    def test_bot_added_to_the_private_chat(self):
        raise AssertionError

    def test_message_to_the_private_chat(self):
        raise AssertionError

    def test_command_as_callback_to_private_chat(self):
        raise AssertionError

    # Group

    def test_bot_added_to_the_group(self):
        raise AssertionError

    def test_bot_kicked_from_the_group_1(self):
        raise AssertionError

    def test_bot_kicked_from_the_group_2(self):
        raise AssertionError

    def test_message_to_the_group(
        self,
    ):  # command as a message needed? special test for /start commend?
        raise AssertionError

    # Channel ?
