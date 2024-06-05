from copy import deepcopy
from unittest import mock

from precisely import assert_that, has_attrs, is_mapping, is_sequence

from telegram_bot.dataclasses import StatusChangeWithinChat
from telegram_bot.enums import MessageType, ChatType, UserActionType
from telegram_bot.parsers import (
    UserMessageParser,
    TelegramCommandParser,
    ChatStatusChangeMessageParser,
)
from telegram_bot.test.base import TelegramBotRequestsTestBase


class TestUserMessageParser(TelegramBotRequestsTestBase):
    def test_parse_message_in_private_chat(self):
        chat_id = 1
        username = "test_username"
        user_id = 2
        text = "test_text"
        first_name = "test_first_name"
        last_name = "test_last_name"

        payload = deepcopy(self.message_in_private_chat_request_payload)
        payload["message"]["chat"]["id"] = chat_id
        payload["message"]["from"]["id"] = user_id
        payload["message"]["from"]["username"] = username
        payload["message"]["text"] = text
        payload["message"]["from"]["first_name"] = first_name
        payload["message"]["from"]["last_name"] = last_name

        serialized_data = self._get_serialized_request_data(payload)
        parsed_data = UserMessageParser.parse(serialized_data)
        assert_that(
            parsed_data,
            has_attrs(
                chat_id=chat_id,
                user_id=user_id,
                username=username,
                text=text,
                first_name=first_name,
                last_name=last_name,
                message_type=MessageType.MESSAGE,
                chat_type=ChatType.PRIVATE,
            ),
        )

    def test_parse_message_in_private_chat_only_id_provided_for_telegram_user(self):
        chat_id = 1
        user_id = 2
        text = "test_text"

        payload = deepcopy(self.message_in_private_chat_request_payload)
        payload["message"]["chat"]["id"] = chat_id
        payload["message"]["from"]["id"] = user_id
        payload["message"]["text"] = text

        del payload["message"]["from"]["username"]
        del payload["message"]["from"]["first_name"]
        del payload["message"]["from"]["last_name"]

        del payload["message"]["chat"]["username"]
        del payload["message"]["chat"]["first_name"]
        del payload["message"]["chat"]["last_name"]

        serialized_data = self._get_serialized_request_data(payload)
        parsed_data = UserMessageParser.parse(serialized_data)
        assert_that(
            parsed_data,
            has_attrs(
                chat_id=chat_id,
                user_id=user_id,
                username=None,
                text=text,
                first_name=None,
                last_name=None,
                message_type=MessageType.MESSAGE,
                chat_type=ChatType.PRIVATE,
            ),
        )


class TestTelegramCommandParser(TelegramBotRequestsTestBase):
    @mock.patch("telegram_bot.parsers.TelegramCommandParser._parse_command_as_message")
    def test_dispatching_in_parse_method_command_as_message_in_private_chat(
        self, mock_method
    ):
        serialized_data = self._get_serialized_request_data(
            self.command_as_message_in_private_chat_request_payload
        )
        TelegramCommandParser.parse(serialized_data)
        mock_method.assert_called_once()
        message_object = serialized_data["message"]
        assert_that(
            mock_method.call_args_list[0].args[0],
            is_mapping(
                {
                    "text": message_object["text"],
                    "entities": is_sequence(is_mapping(message_object["entities"][0])),
                    "from": is_mapping(
                        {
                            "username": message_object["from"]["username"],
                            "first_name": message_object["from"]["first_name"],
                            "last_name": message_object["from"]["last_name"],
                            "id": message_object["from"]["id"],
                            "is_bot": message_object["from"]["is_bot"],
                        }
                    ),
                    "chat": is_mapping(
                        {
                            "id": message_object["chat"]["id"],
                            "type": message_object["chat"]["type"],
                        }
                    ),
                }
            ),
        )

    @mock.patch(
        "telegram_bot.parsers.TelegramCommandParser._parse_command_as_callback_query"
    )
    def test_dispatching_in_parse_method_command_as_callback_in_private_chat(
        self, mock_method
    ):
        serialized_data = self._get_serialized_request_data(
            self.command_as_callback_in_private_chat_request_payload
        )
        TelegramCommandParser.parse(serialized_data)
        mock_method.assert_called_once()
        callback_query = serialized_data["callback_query"]
        assert_that(
            mock_method.call_args_list[0].args[0],
            is_mapping(
                {
                    "data": callback_query["data"],
                    "message": is_mapping(
                        {
                            "chat": is_mapping(
                                {
                                    "id": callback_query["message"]["chat"]["id"],
                                    "type": callback_query["message"]["chat"]["type"],
                                }
                            ),
                            "message_id": callback_query["message"]["message_id"],
                            "reply_markup": is_mapping(
                                {
                                    "inline_keyboard": is_sequence(
                                        is_sequence(
                                            is_mapping(
                                                {
                                                    "callback_data": callback_query[
                                                        "message"
                                                    ]["reply_markup"][
                                                        "inline_keyboard"
                                                    ][
                                                        0
                                                    ][
                                                        0
                                                    ][
                                                        "callback_data"
                                                    ],
                                                    "text": callback_query["message"][
                                                        "reply_markup"
                                                    ]["inline_keyboard"][0][0]["text"],
                                                }
                                            )
                                        )
                                    )
                                }
                            ),
                        }
                    ),
                    "from": is_mapping(
                        {
                            "username": callback_query["from"]["username"],
                            "first_name": callback_query["from"]["first_name"],
                            "last_name": callback_query["from"]["last_name"],
                            "id": callback_query["from"]["id"],
                            "is_bot": callback_query["from"]["is_bot"],
                        }
                    ),
                }
            ),
        )

    @mock.patch("telegram_bot.parsers.TelegramCommandParser._parse_command_as_message")
    def test_dispatching_in_parse_method_command_as_callback_in_group_chat(
        self, mock_method
    ):
        serialized_data = self._get_serialized_request_data(
            self.command_as_message_in_group_request_payload
        )
        TelegramCommandParser.parse(serialized_data)
        mock_method.assert_called_once()
        message_object = serialized_data["message"]
        assert_that(
            mock_method.call_args_list[0].args[0],
            is_mapping(
                {
                    "text": message_object["text"],
                    "entities": is_sequence(is_mapping(message_object["entities"][0])),
                    "from": is_mapping(
                        {
                            "username": message_object["from"]["username"],
                            "first_name": message_object["from"]["first_name"],
                            "last_name": message_object["from"]["last_name"],
                            "id": message_object["from"]["id"],
                            "is_bot": message_object["from"]["is_bot"],
                        }
                    ),
                    "chat": is_mapping(
                        {
                            "id": message_object["chat"]["id"],
                            "type": message_object["chat"]["type"],
                        }
                    ),
                }
            ),
        )


class TestChatStatusChangeMessageParser(TelegramBotRequestsTestBase):
    def test_parse_status_change_bot_added_to_private_chat(self):
        serialized_data = self._get_serialized_request_data(
            self.bot_added_to_the_private_chat_request_payload
        )
        telegram_message = serialized_data.get("my_chat_member") or serialized_data.get(
            "message"
        )
        assert (
            ChatStatusChangeMessageParser._parse_user_action_type(telegram_message)
            == UserActionType.ADD_BOT_TO_CHAT
        )

    def test_parse_status_change_bot_kicked_from_private_chat(self):
        serialized_data = self._get_serialized_request_data(
            self.bot_kicked_from_private_chat_request_payload
        )
        telegram_message = serialized_data.get("my_chat_member") or serialized_data.get(
            "message"
        )
        assert (
            ChatStatusChangeMessageParser._parse_user_action_type(telegram_message)
            == UserActionType.REMOVE_BOT_FROM_CHAT
        )

    def test_parse_status_change_bot_added_to_group_chat(self):
        serialized_data = self._get_serialized_request_data(
            self.bot_added_to_the_group_request_payload
        )
        telegram_message = serialized_data.get("my_chat_member") or serialized_data.get(
            "message"
        )
        assert (
            ChatStatusChangeMessageParser._parse_user_action_type(telegram_message)
            == UserActionType.ADD_BOT_TO_CHAT
        )

    def test_parse_status_change_bot_kicked_from_group_chat_1(self):
        serialized_data = self._get_serialized_request_data(
            self.bot_kicked_from_the_group_request_payload_1
        )
        telegram_message = serialized_data.get("my_chat_member") or serialized_data.get(
            "message"
        )
        assert (
            ChatStatusChangeMessageParser._parse_user_action_type(telegram_message)
            == UserActionType.REMOVE_BOT_FROM_CHAT
        )

    def test_parse_status_change_bot_kicked_from_group_chat_2(self):
        serialized_data = self._get_serialized_request_data(
            self.bot_kicked_from_the_group_request_payload_2
        )
        telegram_message = serialized_data.get("my_chat_member") or serialized_data.get(
            "message"
        )
        assert (
            ChatStatusChangeMessageParser._parse_user_action_type(telegram_message)
            == UserActionType.REMOVE_BOT_FROM_CHAT
        )

    def test_parse_bot_added_to_the_private_chat(self):
        payload = deepcopy(self.bot_added_to_the_private_chat_request_payload)
        del payload["my_chat_member"]["from"]["first_name"]
        del payload["my_chat_member"]["from"]["last_name"]
        del payload["my_chat_member"]["from"]["username"]
        serialized_data = self._get_serialized_request_data(payload)
        parsed_message = ChatStatusChangeMessageParser.parse(serialized_data)
        assert isinstance(parsed_message, StatusChangeWithinChat)
        assert_that(
            parsed_message,
            has_attrs(
                chat_id=payload["my_chat_member"]["chat"]["id"],
                chat_type=ChatType.PRIVATE,
                user_action_type=UserActionType.ADD_BOT_TO_CHAT,
                username=None,
                user_id=payload["my_chat_member"]["from"]["id"],
                first_name=None,
                last_name=None,
            ),
        )

    def test_parse_bot_kicked_from_private_chat(self):
        payload = deepcopy(self.bot_kicked_from_private_chat_request_payload)
        del payload["my_chat_member"]["from"]["first_name"]
        del payload["my_chat_member"]["from"]["last_name"]
        del payload["my_chat_member"]["from"]["username"]
        serialized_data = self._get_serialized_request_data(payload)
        parsed_message = ChatStatusChangeMessageParser.parse(serialized_data)
        assert isinstance(parsed_message, StatusChangeWithinChat)
        assert_that(
            parsed_message,
            has_attrs(
                chat_id=payload["my_chat_member"]["chat"]["id"],
                chat_type=ChatType.PRIVATE,
                user_action_type=UserActionType.REMOVE_BOT_FROM_CHAT,
                username=None,
                user_id=payload["my_chat_member"]["from"]["id"],
                first_name=None,
                last_name=None,
            ),
        )

    def test_parse_bot_added_to_the_group(self):
        payload = deepcopy(self.bot_added_to_the_group_request_payload)
        del payload["my_chat_member"]["from"]["first_name"]
        del payload["my_chat_member"]["from"]["last_name"]
        del payload["my_chat_member"]["from"]["username"]
        serialized_data = self._get_serialized_request_data(payload)
        parsed_message = ChatStatusChangeMessageParser.parse(serialized_data)
        assert isinstance(parsed_message, StatusChangeWithinChat)
        assert_that(
            parsed_message,
            has_attrs(
                chat_id=payload["my_chat_member"]["chat"]["id"],
                chat_type=ChatType.GROUP,
                user_action_type=UserActionType.ADD_BOT_TO_CHAT,
                username=None,
                user_id=payload["my_chat_member"]["from"]["id"],
                first_name=None,
                last_name=None,
            ),
        )

    def test_parse_bot_kicked_from_group_1(self):
        payload = deepcopy(self.bot_kicked_from_the_group_request_payload_1)
        payload["message"]["from"]["first_name"] = "some_first_name"
        payload["message"]["from"]["last_name"] = "some_last_name"
        payload["message"]["from"]["username"] = "some_username"
        serialized_data = self._get_serialized_request_data(payload)
        parsed_message = ChatStatusChangeMessageParser.parse(serialized_data)
        assert isinstance(parsed_message, StatusChangeWithinChat)
        assert_that(
            parsed_message,
            has_attrs(
                chat_id=payload["message"]["chat"]["id"],
                chat_type=ChatType.GROUP,
                user_action_type=UserActionType.REMOVE_BOT_FROM_CHAT,
                username="some_username",
                user_id=payload["message"]["from"]["id"],
                first_name="some_first_name",
                last_name="some_last_name",
            ),
        )

    def test_parse_bot_kicked_from_group_2(self):
        payload = deepcopy(self.bot_kicked_from_the_group_request_payload_2)
        payload["my_chat_member"]["from"]["first_name"] = "some_first_name"
        payload["my_chat_member"]["from"]["last_name"] = "some_last_name"
        payload["my_chat_member"]["from"]["username"] = "some_username"
        serialized_data = self._get_serialized_request_data(payload)
        parsed_message = ChatStatusChangeMessageParser.parse(serialized_data)
        assert isinstance(parsed_message, StatusChangeWithinChat)
        assert_that(
            parsed_message,
            has_attrs(
                chat_id=payload["my_chat_member"]["chat"]["id"],
                chat_type=ChatType.GROUP,
                user_action_type=UserActionType.REMOVE_BOT_FROM_CHAT,
                username="some_username",
                user_id=payload["my_chat_member"]["from"]["id"],
                first_name="some_first_name",
                last_name="some_last_name",
            ),
        )
