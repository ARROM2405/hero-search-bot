import copy
import json

from copy import deepcopy

from precisely import assert_that, is_mapping, has_attrs
from rest_framework import status
from rest_framework.reverse import reverse
from unittest import mock

from telegram_bot.constants import BASE_URL, MESSAGES_MAPPING
from telegram_bot.enums import UserActionType, ChatType
from telegram_bot.messages_texts import (
    FIRST_INSTRUCTIONS,
    INPUT_CONFIRMED_RESPONSE,
    EDITED_MESSAGE_RESPONSE,
)
from telegram_bot.models import TelegramUser, BotStatusChange
from telegram_bot.test.base import TelegramBotRequestsTestBase


class TestTelegramBotApiViewSet(TelegramBotRequestsTestBase):
    def setUp(self):
        super().setUp()
        self.url = reverse("telegram_bot:telegram_bot-user-message")

    # Private chat

    @mock.patch("telegram_bot.message_handling_services.requests.post")
    def test_start_command_in_the_private_chat(self, mock_post):
        payload = deepcopy(self.command_as_message_in_private_chat_request_payload)
        chat_id_from_the_command = payload["message"]["chat"]["id"]

        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == status.HTTP_200_OK
        mock_post.assert_called_with(
            url=BASE_URL + "sendMessage",
            data={
                "chat_id": chat_id_from_the_command,
                "text": FIRST_INSTRUCTIONS,
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
            },
        )

    @mock.patch("telegram_bot.message_handling_services.requests.post")
    def test_bot_kicked_from_the_private_chat(self, mock_post):
        user_data = self.bot_kicked_from_private_chat_request_payload["my_chat_member"][
            "chat"
        ]
        first_name = user_data["first_name"]
        last_name = user_data["last_name"]
        username = user_data["username"]
        telegram_id = user_data["id"]

        response = self.client.post(
            self.url,
            data=json.dumps(self.bot_kicked_from_private_chat_request_payload),
            content_type="application/json",
        )

        assert response.status_code == status.HTTP_200_OK
        mock_post.assert_not_called()

        created_user = TelegramUser.objects.get()
        assert_that(
            created_user,
            has_attrs(
                first_name=first_name,
                last_name=last_name,
                username=username,
                telegram_id=telegram_id,
            ),
        )
        assert_that(
            BotStatusChange.objects.get(),
            has_attrs(
                initiator=created_user,
                chat_id=telegram_id,
                action_type=UserActionType.REMOVE_BOT_FROM_CHAT,
                chat_type=ChatType.PRIVATE,
            ),
        )

    @mock.patch("telegram_bot.message_handling_services.requests.post")
    def test_bot_added_to_the_private_chat(self, mock_post):
        user_data = self.bot_added_to_the_private_chat_request_payload[
            "my_chat_member"
        ]["chat"]
        first_name = user_data["first_name"]
        last_name = user_data["last_name"]
        username = user_data["username"]
        telegram_id = user_data["id"]

        response = self.client.post(
            self.url,
            data=json.dumps(self.bot_added_to_the_private_chat_request_payload),
            content_type="application/json",
        )

        assert response.status_code == status.HTTP_200_OK
        mock_post.assert_not_called()

        created_user = TelegramUser.objects.get()
        assert_that(
            created_user,
            has_attrs(
                first_name=first_name,
                last_name=last_name,
                username=username,
                telegram_id=telegram_id,
            ),
        )
        assert_that(
            BotStatusChange.objects.get(),
            has_attrs(
                initiator=created_user,
                chat_id=telegram_id,
                action_type=UserActionType.ADD_BOT_TO_CHAT,
                chat_type=ChatType.PRIVATE,
            ),
        )

    @mock.patch(
        "telegram_bot.message_handling_services.SequentialMessagesProcessor.get_response_text"
    )
    @mock.patch("telegram_bot.message_handling_services.requests.post")
    def test_message_to_the_private_chat(self, mock_post, mock_get_response_text):
        response_text = MESSAGES_MAPPING["hero_last_name"]

        mock_get_response_text.return_value = response_text

        response = self.client.post(
            self.url,
            data=json.dumps(self.message_in_private_chat_request_payload),
            content_type="application/json",
        )

        assert response.status_code == status.HTTP_200_OK
        mock_post.assert_called_once_with(
            url=BASE_URL + "sendMessage",
            data={
                "chat_id": self.message_in_private_chat_request_payload["message"][
                    "chat"
                ]["id"],
                "text": response_text,
            },
        )

    @mock.patch(
        "telegram_bot.message_handling_services.SequentialMessagesProcessor.check_if_user_input_exists"
    )
    @mock.patch(
        "telegram_bot.message_handling_services.SequentialMessagesProcessor.get_response_text"
    )
    @mock.patch("telegram_bot.message_handling_services.requests.post")
    def test_edited_message_to_the_private_chat(
        self, mock_post, mock_get_response_text, mock_check_if_user_input_exists
    ):
        mock_check_if_user_input_exists.return_value = True
        response_text = EDITED_MESSAGE_RESPONSE
        mock_get_response_text.return_value = response_text
        response = self.client.post(
            self.url,
            data=json.dumps(self.edited_message_in_private_chat_request_payload),
            content_type="application/json",
        )

        assert response.status_code == status.HTTP_200_OK

        mock_post.assert_called_once_with(
            url=BASE_URL + "sendMessage",
            data={
                "chat_id": self.edited_message_in_private_chat_request_payload[
                    "edited_message"
                ]["chat"]["id"],
                "text": response_text,
                "reply_markup": json.dumps(
                    {
                        "inline_keyboard": [
                            [
                                {
                                    "text": "Почати вводити дані з початку.",
                                    "callback_data": "/remove_and_restart_input",
                                }
                            ],
                            [
                                {
                                    "text": "Продовжую як є.",
                                    "callback_data": "/continue_input",
                                }
                            ],
                        ],
                    }
                ),
            },
        )

    @mock.patch(
        "telegram_bot.message_handling_services.SequentialMessagesProcessor.save_confirmed_data"
    )
    @mock.patch("telegram_bot.message_handling_services.requests.post")
    def test_command_as_callback_to_private_chat(
        self, mock_post, mock_save_confirmed_data
    ):
        payload = deepcopy(self.command_as_callback_in_private_chat_request_payload)
        payload["callback_query"]["data"] = "/input_confirmed"

        user_data = payload["callback_query"]["from"]

        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert mock_post.call_count == 2

        assert_that(
            mock_post.mock_calls[0].kwargs,
            is_mapping(
                {
                    "url": BASE_URL + "editMessageReplyMarkup",
                    "json": is_mapping(
                        {
                            "chat_id": user_data["id"],
                            "message_id": payload["callback_query"]["message"][
                                "message_id"
                            ],
                            "reply_markup": {"inline_keyboard": []},
                        }
                    ),
                }
            ),
        )

        assert_that(
            mock_post.mock_calls[1].kwargs,
            is_mapping(
                {
                    "url": BASE_URL + "sendMessage",
                    "data": is_mapping(
                        {
                            "chat_id": user_data["id"],
                            "text": INPUT_CONFIRMED_RESPONSE,
                        }
                    ),
                }
            ),
        )

        created_user = TelegramUser.objects.get()
        assert_that(
            created_user,
            has_attrs(
                telegram_id=user_data["id"],
                username=user_data["username"],
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
            ),
        )
        mock_save_confirmed_data.assert_called_once_with(
            user_id=user_data["id"],
            entry_author=created_user,
        )

    # Group

    @mock.patch("telegram_bot.message_handling_services.requests.post")
    def test_bot_added_to_the_group(self, mock_post):
        user_data = self.bot_added_to_the_group_request_payload["my_chat_member"][
            "from"
        ]
        first_name = user_data["first_name"]
        last_name = user_data["last_name"]
        username = user_data["username"]
        telegram_id = user_data["id"]

        response = self.client.post(
            self.url,
            data=json.dumps(self.bot_added_to_the_group_request_payload),
            content_type="application/json",
        )

        assert response.status_code == status.HTTP_200_OK
        mock_post.assert_not_called()

        created_user = TelegramUser.objects.get()
        assert_that(
            created_user,
            has_attrs(
                first_name=first_name,
                last_name=last_name,
                username=username,
                telegram_id=telegram_id,
            ),
        )
        assert_that(
            BotStatusChange.objects.get(),
            has_attrs(
                initiator=created_user,
                chat_id=self.bot_added_to_the_group_request_payload["my_chat_member"][
                    "chat"
                ]["id"],
                action_type=UserActionType.ADD_BOT_TO_CHAT,
                chat_type=ChatType.GROUP,
            ),
        )

    @mock.patch("telegram_bot.message_handling_services.requests.post")
    def test_bot_kicked_from_the_group_1(self, mock_post):
        user_data = self.bot_kicked_from_the_group_request_payload_1["message"]["from"]
        first_name = user_data["first_name"]
        last_name = user_data["last_name"]
        username = user_data["username"]
        telegram_id = user_data["id"]

        response = self.client.post(
            self.url,
            data=json.dumps(self.bot_kicked_from_the_group_request_payload_1),
            content_type="application/json",
        )

        assert response.status_code == status.HTTP_200_OK
        mock_post.assert_not_called()

        created_user = TelegramUser.objects.get()
        assert_that(
            created_user,
            has_attrs(
                first_name=first_name,
                last_name=last_name,
                username=username,
                telegram_id=telegram_id,
            ),
        )
        assert_that(
            BotStatusChange.objects.get(),
            has_attrs(
                initiator=created_user,
                chat_id=self.bot_kicked_from_the_group_request_payload_1["message"][
                    "chat"
                ]["id"],
                action_type=UserActionType.REMOVE_BOT_FROM_CHAT,
                chat_type=ChatType.GROUP,
            ),
        )

    @mock.patch("telegram_bot.message_handling_services.requests.post")
    def test_bot_kicked_from_the_group_2(self, mock_post):
        user_data = self.bot_kicked_from_the_group_request_payload_2["my_chat_member"][
            "from"
        ]
        first_name = user_data["first_name"]
        last_name = user_data["last_name"]
        username = user_data["username"]
        telegram_id = user_data["id"]

        response = self.client.post(
            self.url,
            data=json.dumps(self.bot_kicked_from_the_group_request_payload_2),
            content_type="application/json",
        )

        assert response.status_code == status.HTTP_200_OK
        mock_post.assert_not_called()

        created_user = TelegramUser.objects.get()
        assert_that(
            created_user,
            has_attrs(
                first_name=first_name,
                last_name=last_name,
                username=username,
                telegram_id=telegram_id,
            ),
        )
        assert_that(
            BotStatusChange.objects.get(),
            has_attrs(
                initiator=created_user,
                chat_id=self.bot_kicked_from_the_group_request_payload_2[
                    "my_chat_member"
                ]["chat"]["id"],
                action_type=UserActionType.REMOVE_BOT_FROM_CHAT,
                chat_type=ChatType.GROUP,
            ),
        )

    @mock.patch("telegram_bot.message_handling_services.requests.post")
    def test_command_as_message_to_the_group(self, mock_post):
        self.client.post(
            self.url,
            data=json.dumps(self.command_as_message_in_group_request_payload),
            content_type="application/json",
        ),

        mock_post.assert_not_called()

    @mock.patch("telegram_bot.message_handling_services.requests.post")
    def test_unknown_command_returns_200(self, mock_post):
        payload = copy.deepcopy(self.command_as_message_in_group_request_payload)
        payload["message"]["text"] = "/unknown_command"
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == status.HTTP_200_OK
