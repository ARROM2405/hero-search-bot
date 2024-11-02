import copy
import json
import os
from unittest import mock

from django.test import override_settings
from precisely import assert_that, has_attrs, is_mapping, is_sequence

from telegram_bot.constants import (
    ORDER_OF_MESSAGES,
    MESSAGES_MAPPING,
    BASE_URL,
    MESSAGE_TEXT_VALIDATION_FAILED,
)
from telegram_bot.enums import ChatType, UserActionType
from telegram_bot.exceptions import (
    TelegramMessageNotParsedException,
    UnknownCommandException,
    UnauthorizedUserCalledReportGenerationException,
)
from telegram_bot.message_handling_services import (
    MessageHandler,
    MemberStatusChangeProcessor,
    BotCommandProcessor,
    UserMessageProcessor,
)
from telegram_bot.messages_texts import (
    FIRST_INSTRUCTIONS,
    ALL_DATA_RECEIVED_RESPONSE,
    INQUERY_MESSAGE_START,
    CASE_ID_INQUERY,
    INPUT_CONFIRMED_RESPONSE,
    INPUT_NOT_CONFIRMED_RESPONSE,
    EDITED_MESSAGE_RESPONSE,
)
from telegram_bot.models import BotStatusChange, TelegramUser
from telegram_bot.parsers import UserMessageParser, TelegramCommandParser
from telegram_bot.sequential_messages_processor import SequentialMessagesProcessor
from telegram_bot.test.base import TelegramBotRequestsTestBase


class TestMessageHandler(TelegramBotRequestsTestBase):

    # Private chat

    def test_get_message_processor_for_bot_added_to_private_chat_action(self):
        serialized_data = self._get_serialized_request_data(
            self.bot_added_to_the_private_chat_request_payload
        )
        message_handler = MessageHandler(telegram_message=serialized_data)
        processor = message_handler._get_message_processor()
        assert isinstance(processor, MemberStatusChangeProcessor)

    def test_get_message_processor_for_bot_kicked_to_private_chat_action(self):
        serialized_data = self._get_serialized_request_data(
            self.bot_kicked_from_private_chat_request_payload
        )
        message_handler = MessageHandler(telegram_message=serialized_data)
        processor = message_handler._get_message_processor()
        assert isinstance(processor, MemberStatusChangeProcessor)

    def test_get_message_processor_for_command_as_message_in_private_chat(self):
        serialized_data = self._get_serialized_request_data(
            self.command_as_message_in_private_chat_request_payload
        )
        message_handler = MessageHandler(telegram_message=serialized_data)
        processor = message_handler._get_message_processor()
        assert isinstance(processor, BotCommandProcessor)

    def test_get_message_processor_for_command_as_callback_in_private_chat(self):
        serialized_data = self._get_serialized_request_data(
            self.command_as_callback_in_private_chat_request_payload
        )
        message_handler = MessageHandler(telegram_message=serialized_data)
        processor = message_handler._get_message_processor()
        assert isinstance(processor, BotCommandProcessor)

    def test_get_message_processor_for_message_in_private_chat(self):
        serialized_data = self._get_serialized_request_data(
            self.message_in_private_chat_request_payload
        )
        message_handler = MessageHandler(telegram_message=serialized_data)
        processor = message_handler._get_message_processor()
        assert isinstance(processor, UserMessageProcessor)

    # Group

    def test_get_message_processor_for_bot_added_to_group_action(self):
        serialized_data = self._get_serialized_request_data(
            self.bot_added_to_the_group_request_payload
        )
        message_handler = MessageHandler(telegram_message=serialized_data)
        processor = message_handler._get_message_processor()
        assert isinstance(processor, MemberStatusChangeProcessor)

    def test_get_message_processor_for_bot_kicked_from_group_action_1(self):
        serialized_data = self._get_serialized_request_data(
            self.bot_kicked_from_the_group_request_payload_1
        )
        message_handler = MessageHandler(telegram_message=serialized_data)
        processor = message_handler._get_message_processor()
        assert isinstance(processor, MemberStatusChangeProcessor)

    def test_get_message_processor_for_bot_kicked_from_group_action_2(self):
        serialized_data = self._get_serialized_request_data(
            self.bot_kicked_from_the_group_request_payload_2
        )
        message_handler = MessageHandler(telegram_message=serialized_data)
        processor = message_handler._get_message_processor()
        assert isinstance(processor, MemberStatusChangeProcessor)

    def test_get_message_processor_for_command_as_message_in_group_chat(self):
        serialized_data = self._get_serialized_request_data(
            self.command_as_message_in_group_request_payload
        )
        message_handler = MessageHandler(telegram_message=serialized_data)
        processor = message_handler._get_message_processor()
        assert isinstance(processor, BotCommandProcessor)

    # Handle message method

    @mock.patch("telegram_bot.message_handling_services.requests.post")
    def test_handle_telegram_message_start_command_in_private_chat(
        self, post_request_mock
    ):
        serialized_data = self._get_serialized_request_data(
            self.command_as_message_in_private_chat_request_payload
        )
        message_handler = MessageHandler(telegram_message=serialized_data)
        message_handler.handle_telegram_message()
        post_request_mock.assert_called_once()
        mock_called_with_kwargs = post_request_mock.call_args_list[0].kwargs["data"]
        assert mock_called_with_kwargs["text"] == FIRST_INSTRUCTIONS
        assert "inline_keyboard" in mock_called_with_kwargs["reply_markup"]

    @mock.patch(
        "telegram_bot.message_handling_services.SequentialMessagesProcessor.get_response_text"
    )
    @mock.patch(
        "telegram_bot.message_handling_services.SequentialMessagesProcessor.get_user_input"
    )
    @mock.patch("telegram_bot.message_handling_services.requests.post")
    def test_handle_telegram_user_message_in_private_chat(
        self,
        post_request_mock,
        get_user_input_mock,
        get_response_text_mock,
    ):
        get_user_input_mock.return_value = {b"empty": "True"}
        response_text = "some response text"
        get_response_text_mock.return_value = response_text

        serialized_data = self._get_serialized_request_data(
            self.message_in_private_chat_request_payload
        )
        message_handler = MessageHandler(telegram_message=serialized_data)
        message_handler.handle_telegram_message()

        post_request_mock.assert_called_once()
        mock_called_with_kwargs = post_request_mock.call_args_list[0].kwargs["data"]
        assert mock_called_with_kwargs["text"] == response_text
        assert "reply_markup" not in mock_called_with_kwargs


class TestMemberStatusChangeProcessor(TelegramBotRequestsTestBase):
    def test_process_bot_added_to_the_private_chat(self):
        initiator_username = "initiator_username"
        chat_id = 123123123
        self.bot_added_to_the_private_chat_request_payload["my_chat_member"]["from"][
            "username"
        ] = initiator_username
        self.bot_added_to_the_private_chat_request_payload["my_chat_member"]["from"][
            "last_name"
        ] = None
        self.bot_added_to_the_private_chat_request_payload["my_chat_member"]["chat"][
            "id"
        ] = chat_id
        serialized_request_data = self._get_serialized_request_data(
            self.bot_added_to_the_private_chat_request_payload
        )
        processor = MemberStatusChangeProcessor(serialized_request_data)
        processor.process()
        bot_status_change_entry = BotStatusChange.objects.get()
        initiator = TelegramUser.objects.get()
        assert initiator.username == initiator_username
        assert_that(
            bot_status_change_entry,
            has_attrs(
                initiator=initiator,
                action_type=UserActionType.ADD_BOT_TO_CHAT,
                chat_type=ChatType.PRIVATE,
                chat_id=chat_id,
            ),
        )

    def test_process_bot_kicked_from_private_chat(self):
        initiator_username = self.bot_kicked_from_private_chat_request_payload[
            "my_chat_member"
        ]["from"]["username"]
        chat_id = self.bot_kicked_from_private_chat_request_payload["my_chat_member"][
            "chat"
        ]["id"]
        serialized_request_data = self._get_serialized_request_data(
            self.bot_kicked_from_private_chat_request_payload
        )
        processor = MemberStatusChangeProcessor(serialized_request_data)
        processor.process()
        bot_status_change_entry = BotStatusChange.objects.get()
        initiator = TelegramUser.objects.get()
        assert initiator.username == initiator_username
        assert_that(
            bot_status_change_entry,
            has_attrs(
                initiator=initiator,
                action_type=UserActionType.REMOVE_BOT_FROM_CHAT,
                chat_type=ChatType.PRIVATE,
                chat_id=chat_id,
            ),
        )

    def test_process_bot_added_to_the_group(self):
        initiator_username = self.bot_added_to_the_group_request_payload[
            "my_chat_member"
        ]["from"]["username"]
        chat_id = self.bot_added_to_the_group_request_payload["my_chat_member"]["chat"][
            "id"
        ]
        serialized_request_data = self._get_serialized_request_data(
            self.bot_added_to_the_group_request_payload
        )
        processor = MemberStatusChangeProcessor(serialized_request_data)
        processor.process()
        bot_status_change_entry = BotStatusChange.objects.get()
        initiator = TelegramUser.objects.get()
        assert initiator.username == initiator_username
        assert_that(
            bot_status_change_entry,
            has_attrs(
                initiator=initiator,
                action_type=UserActionType.ADD_BOT_TO_CHAT,
                chat_type=ChatType.GROUP,
                chat_id=chat_id,
            ),
        )

    def test_process_bot_kicked_from_the_group_request_format_1(self):
        initiator_username = self.bot_kicked_from_the_group_request_payload_1[
            "message"
        ]["from"]["username"]
        chat_id = self.bot_kicked_from_the_group_request_payload_1["message"]["chat"][
            "id"
        ]
        serialized_request_data = self._get_serialized_request_data(
            self.bot_kicked_from_the_group_request_payload_1
        )
        processor = MemberStatusChangeProcessor(serialized_request_data)
        processor.process()
        bot_status_change_entry = BotStatusChange.objects.get()
        initiator = TelegramUser.objects.get()
        assert initiator.username == initiator_username
        assert_that(
            bot_status_change_entry,
            has_attrs(
                initiator=initiator,
                action_type=UserActionType.REMOVE_BOT_FROM_CHAT,
                chat_type=ChatType.GROUP,
                chat_id=chat_id,
            ),
        )

    def test_process_bot_kicked_from_the_group_request_format_2(self):
        initiator_username = self.bot_kicked_from_the_group_request_payload_2[
            "my_chat_member"
        ]["from"]["username"]
        chat_id = self.bot_kicked_from_the_group_request_payload_2["my_chat_member"][
            "chat"
        ]["id"]
        serialized_request_data = self._get_serialized_request_data(
            self.bot_kicked_from_the_group_request_payload_2
        )
        processor = MemberStatusChangeProcessor(serialized_request_data)
        processor.process()
        bot_status_change_entry = BotStatusChange.objects.get()
        initiator = TelegramUser.objects.get()
        assert initiator.username == initiator_username
        assert_that(
            bot_status_change_entry,
            has_attrs(
                initiator=initiator,
                action_type=UserActionType.REMOVE_BOT_FROM_CHAT,
                chat_type=ChatType.GROUP,
                chat_id=chat_id,
            ),
        )


class TestUserMessageProcessor(TelegramBotRequestsTestBase):

    @mock.patch("telegram_bot.sequential_messages_processor.redis.Redis.hgetall")
    def test_prepare_sequential_messages_processor(self, redis_hgetall_mock):
        redis_hgetall_mock.return_value = {}
        serialized_request_data = self._get_serialized_request_data(
            self.message_in_private_chat_request_payload
        )
        parsed_user_message = UserMessageParser.parse(serialized_request_data)
        processor = UserMessageProcessor(serialized_request_data)
        processor.parsed_telegram_message = parsed_user_message
        processor._prepare_sequential_messages_processor()
        assert isinstance(
            processor.sequential_messages_processor, SequentialMessagesProcessor
        )
        assert processor.sequential_messages_processor.current_message_key == "case_id"
        assert (
            processor.sequential_messages_processor.next_message_key == "hero_last_name"
        )

    def test_prepare_sequential_messages_processor_no_parsed_message(self):
        serialized_request_data = self._get_serialized_request_data(
            self.message_in_private_chat_request_payload
        )
        processor = UserMessageProcessor(serialized_request_data)
        with self.assertRaises(TelegramMessageNotParsedException):
            processor._prepare_sequential_messages_processor()

    @mock.patch("telegram_bot.sequential_messages_processor.redis.Redis.hgetall")
    def test_prepare_sequential_messages_processor_all_data_received(
        self, redis_hgetall_mock
    ):
        redis_hgetall_mock.return_value = {
            key.encode(): None for key in ORDER_OF_MESSAGES
        }
        serialized_request_data = self._get_serialized_request_data(
            self.message_in_private_chat_request_payload
        )
        parsed_user_message = UserMessageParser.parse(serialized_request_data)
        processor = UserMessageProcessor(serialized_request_data)
        processor.parsed_telegram_message = parsed_user_message
        processor.process()
        assert processor.all_data_received is True

    def test_process(self):
        chat_id = self.message_in_private_chat_request_payload["message"]["chat"]["id"]
        message_text = self.message_in_private_chat_request_payload["message"]["text"]
        payload = copy.deepcopy(self.message_in_private_chat_request_payload)
        del payload["message"]["from"]["username"]
        del payload["message"]["from"]["last_name"]

        with self.subTest():
            with mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hgetall",
            ) as hgetall_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hset"
            ) as hset_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.SequentialMessagesProcessor.check_if_user_input_exists"
            ) as check_if_user_input_exists_mock:
                check_if_user_input_exists_mock.return_value = True
                hgetall_mock.return_value = {b"empty": "True"}
                serialized_request_data = self._get_serialized_request_data(payload)
                processor = UserMessageProcessor(serialized_request_data)
                processor.process()
                hgetall_mock.assert_called_once()
                hset_mock.assert_called_once_with(
                    str(chat_id), mapping={"case_id": message_text}
                )
                assert processor.all_data_received is False

        with self.subTest():
            with mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hgetall",
            ) as hgetall_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hset"
            ) as hset_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.SequentialMessagesProcessor.check_if_user_input_exists"
            ) as check_if_user_input_exists_mock:
                check_if_user_input_exists_mock.return_value = True
                hgetall_mock.return_value = {"case_id".encode(): None}
                serialized_request_data = self._get_serialized_request_data(payload)
                processor = UserMessageProcessor(serialized_request_data)
                processor.process()
                hgetall_mock.assert_called_once()
                hset_mock.assert_called_once_with(
                    str(chat_id), mapping={"hero_last_name": message_text}
                )
                assert processor.all_data_received is False

        with self.subTest():
            with mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hgetall",
            ) as hgetall_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hset"
            ) as hset_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.expire"
            ) as expire_mock:
                hgetall_mock.return_value = {
                    "case_id".encode(): None,
                    "hero_last_name".encode(): None,
                    "hero_first_name".encode(): None,
                    "hero_patronymic".encode(): None,
                    "hero_date_of_birth".encode(): None,
                    "item_used_for_dna_extraction".encode(): None,
                    "relative_last_name".encode(): None,
                    "relative_first_name".encode(): None,
                    "relative_patronymic".encode(): None,
                    "is_added_to_dna_db".encode(): None,
                    "comment".encode(): None,
                }
                serialized_request_data = self._get_serialized_request_data(payload)
                processor = UserMessageProcessor(serialized_request_data)
                processor.process()
                hgetall_mock.assert_called_once()
                hset_mock.assert_not_called()
                expire_mock.assert_not_called()
                assert processor.all_data_received is True

    @mock.patch(
        "telegram_bot.message_handling_services.SequentialMessagesProcessor.save_message"
    )
    def test_process_edited_message_is_not_saved(self, mock_save_message):
        serialized_request_data = self._get_serialized_request_data(
            self.edited_message_in_private_chat_request_payload
        )
        processor = UserMessageProcessor(serialized_request_data)
        processor.process()
        mock_save_message.assert_not_called()

    def test_prepare_response_user_message_in_private_chat(self):
        chat_id = self.message_in_private_chat_request_payload["message"]["chat"]["id"]
        payload = copy.deepcopy(self.message_in_private_chat_request_payload)
        del payload["message"]["from"]["first_name"]
        del payload["message"]["from"]["last_name"]

        with self.subTest():
            # message_validation_failed
            with mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hgetall",
            ) as hgetall_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hset"
            ) as hset_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.expire"
            ) as expire_mock:
                hgetall_mock.return_value = {
                    b"case_id": "123123",
                    b"hero_last_name": "AAA",
                    b"hero_first_name": "BBB",
                    b"hero_patronymic": "CCC",
                }
                payload["message"]["text"] = "1.2.2000"
                serialized_request_data = self._get_serialized_request_data(payload)
                processor = UserMessageProcessor(serialized_request_data)
                processor.process()
                response_object = processor.prepare_response()
                assert_that(
                    response_object,
                    is_mapping(
                        {
                            "data": is_mapping(
                                {
                                    "text": f"{MESSAGE_TEXT_VALIDATION_FAILED}\n{MESSAGES_MAPPING['hero_date_of_birth']}",
                                    "chat_id": chat_id,
                                    "reply_markup": json.dumps(
                                        {
                                            "inline_keyboard": [
                                                {
                                                    "text": "Почати вводити дані з початку.",
                                                    "callback_data": "/start",
                                                }
                                            ],
                                        },
                                    ),
                                }
                            ),
                        }
                    ),
                )
                hset_mock.assert_not_called()

        with self.subTest():
            with mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hgetall",
            ) as hgetall_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hset"
            ) as hset_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.expire"
            ) as expire_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.SequentialMessagesProcessor.check_if_user_input_exists"
            ) as check_if_user_input_exists_mock:
                hgetall_mock.return_value = {}
                serialized_request_data = self._get_serialized_request_data(payload)
                processor = UserMessageProcessor(serialized_request_data)
                processor.process()
                response_object = processor.prepare_response()
                assert_that(
                    response_object,
                    is_mapping(
                        {
                            "data": is_mapping(
                                {
                                    "text": MESSAGES_MAPPING["hero_last_name"],
                                    "chat_id": chat_id,
                                }
                            )
                        }
                    ),
                )

        with self.subTest():
            with mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hgetall",
            ) as hgetall_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hset"
            ) as hset_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.expire"
            ) as expire_mock:
                hgetall_mock.return_value = {
                    "case_id".encode(): None,
                    "hero_last_name".encode(): None,
                }
                serialized_request_data = self._get_serialized_request_data(payload)
                processor = UserMessageProcessor(serialized_request_data)
                processor.process()
                response_object = processor.prepare_response()
                assert_that(
                    response_object,
                    is_mapping(
                        {
                            "data": is_mapping(
                                {
                                    "text": MESSAGES_MAPPING["hero_patronymic"],
                                    "chat_id": chat_id,
                                }
                            )
                        }
                    ),
                )

        with self.subTest():
            with mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hgetall",
            ) as hgetall_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hset"
            ) as hset_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.expire"
            ) as expire_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.SequentialMessagesProcessor.check_if_user_input_exists"
            ) as check_if_user_input_exists_mock:
                check_if_user_input_exists_mock.return_value = True
                hgetall_mock.side_effect = [
                    {
                        "case_id".encode(): "some_case_id".encode(),
                        "hero_last_name".encode(): "some_hero_last_name".encode(),
                        "hero_first_name".encode(): "some_hero_first_name".encode(),
                        "hero_patronymic".encode(): "some_hero_patronymic".encode(),
                        "hero_date_of_birth".encode(): "some_hero_date_of_birth".encode(),
                        "item_used_for_dna_extraction".encode(): "some_item_used_for_dna_extraction".encode(),
                        "relative_last_name".encode(): "some_relative_last_name".encode(),
                        "relative_first_name".encode(): "some_relative_first_name".encode(),
                        "relative_patronymic".encode(): "some_relative_patronymic".encode(),
                        "is_added_to_dna_db".encode(): "some_is_added_to_dna_db".encode(),
                    },
                    {
                        "case_id".encode(): "some_case_id".encode(),
                        "hero_last_name".encode(): "some_hero_last_name".encode(),
                        "hero_first_name".encode(): "some_hero_first_name".encode(),
                        "hero_patronymic".encode(): "some_hero_patronymic".encode(),
                        "hero_date_of_birth".encode(): "some_hero_date_of_birth".encode(),
                        "item_used_for_dna_extraction".encode(): "some_item_used_for_dna_extraction".encode(),
                        "relative_last_name".encode(): "some_relative_last_name".encode(),
                        "relative_first_name".encode(): "some_relative_first_name".encode(),
                        "relative_patronymic".encode(): "some_relative_patronymic".encode(),
                        "is_added_to_dna_db".encode(): "some_is_added_to_dna_db".encode(),
                        "comment".encode(): "some_comment".encode(),
                    },
                ]
                serialized_request_data = self._get_serialized_request_data(payload)
                processor = UserMessageProcessor(serialized_request_data)
                processor.process()
                response_object = processor.prepare_response()
                assert_that(
                    response_object,
                    is_mapping(
                        {
                            "data": is_mapping(
                                {
                                    "text": f"""Будьласка підтвердіть чи всі введені дані коректні.
        Номер справи в реєстрі: some_case_id
        Прізвище героя: some_hero_last_name
        Ім'я героя: some_hero_first_name
        Ім'я по батькові героя: some_hero_patronymic
        Дата народження героя: some_hero_date_of_birth
        Предмет використания для отримання зразка ДНК: some_item_used_for_dna_extraction
        Прізвище родича: some_relative_last_name
        Ім'я родича: some_relative_first_name
        Ім'я по батькові родича: some_relative_patronymic
        Дані є в реєстрі ДНК: some_is_added_to_dna_db
        Коментар: some_comment
        """,
                                    "chat_id": chat_id,
                                    "reply_markup": json.dumps(
                                        {
                                            "inline_keyboard": [
                                                [
                                                    {
                                                        "text": "Дані корректні.",
                                                        "callback_data": "/input_confirmed",
                                                    }
                                                ],
                                                [
                                                    {
                                                        "text": "Дані не корректні. Маю відредагувати.",
                                                        "callback_data": "/input_not_confirmed",
                                                    }
                                                ],
                                            ],
                                        }
                                    ),
                                }
                            )
                        }
                    ),
                )

        with self.subTest():
            with mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hgetall",
            ) as hgetall_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hset"
            ) as hset_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.expire"
            ) as expire_mock:
                hgetall_mock.return_value = {
                    "case_id".encode(): None,
                    "hero_last_name".encode(): None,
                    "hero_first_name".encode(): None,
                    "hero_patronymic".encode(): None,
                    "hero_date_of_birth".encode(): None,
                    "item_used_for_dna_extraction".encode(): None,
                    "relative_last_name".encode(): None,
                    "relative_first_name".encode(): None,
                    "relative_patronymic".encode(): None,
                    "is_added_to_dna_db".encode(): None,
                    "comment".encode(): None,
                }
                serialized_request_data = self._get_serialized_request_data(payload)
                processor = UserMessageProcessor(serialized_request_data)
                processor.process()
                response_object = processor.prepare_response()
                assert_that(
                    response_object,
                    is_mapping(
                        {
                            "data": is_mapping(
                                {
                                    "text": ALL_DATA_RECEIVED_RESPONSE,
                                    "chat_id": chat_id,
                                }
                            )
                        }
                    ),
                )
        with self.subTest():
            with mock.patch(
                "telegram_bot.message_handling_services.SequentialMessagesProcessor.check_if_user_input_exists",
            ) as mock_check_if_user_input_exists, mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hgetall",
            ) as hgetall_mock:
                mock_check_if_user_input_exists.return_value = True
                hgetall_mock.return_value = {"case_id".encode(): None}
                serialized_request_data = self._get_serialized_request_data(
                    self.edited_message_in_private_chat_request_payload
                )
                processor = UserMessageProcessor(serialized_request_data)
                processor.process()
                response_object = processor.prepare_response()
                assert_that(
                    response_object,
                    is_mapping(
                        {
                            "data": is_mapping(
                                {
                                    "chat_id": self.edited_message_in_private_chat_request_payload[
                                        "edited_message"
                                    ][
                                        "chat"
                                    ][
                                        "id"
                                    ],
                                    "text": EDITED_MESSAGE_RESPONSE,
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
                                }
                            )
                        }
                    ),
                )


class TestBotCommandProcessor(TelegramBotRequestsTestBase):

    def setUp(self):
        super().setUp()
        self.chat_id = 1
        self.message_id = 2

    @mock.patch("telegram_bot.message_handling_services.requests.post")
    def test_remove_inline_keyboard_from_replied_message(self, mock_post):
        payload = copy.deepcopy(
            self.command_as_callback_in_private_chat_request_payload
        )
        payload["callback_query"]["message"]["chat"]["id"] = self.chat_id
        payload["callback_query"]["message"]["id"] = self.message_id

        serialized_data = self._get_serialized_request_data(payload)
        processor = BotCommandProcessor(serialized_data)
        processor._remove_inline_keyboard_from_replied_message(
            self.chat_id, self.message_id
        )
        mock_post.assert_called_once_with(
            url=BASE_URL + "editMessageReplyMarkup",
            json={
                "chat_id": self.chat_id,
                "message_id": self.message_id,
                "reply_markup": {"inline_keyboard": []},
            },
        )

    # process method

    # command: /start
    @mock.patch(
        "telegram_bot.message_handling_services.SequentialMessagesProcessor.delete_user_input"
    )
    def test_process_start(self, mock_delete_user_input):
        serialized_data = self._get_serialized_request_data(
            self.command_as_message_in_private_chat_request_payload
        )
        parsed_message = TelegramCommandParser.parse(serialized_data)

        processor = BotCommandProcessor(telegram_message={})
        processor.parsed_telegram_message = parsed_message
        processor._process_start_command()
        mock_delete_user_input.assert_called_once_with(
            serialized_data["message"]["chat"]["id"]
        )

    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._remove_inline_keyboard_from_replied_message"
    )
    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._process_start_command"
    )
    def test_process_start_command_in_the_private_chat_as_a_message(
        self,
        mock_process_command,
        mock_remove_inline_keyboard,
    ):
        serialized_data = self._get_serialized_request_data(
            self.command_as_message_in_private_chat_request_payload
        )
        processor = BotCommandProcessor(serialized_data)
        processor.process()
        mock_process_command.assert_called_once()
        mock_remove_inline_keyboard.assert_not_called()

    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._remove_inline_keyboard_from_replied_message"
    )
    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._process_start_command"
    )
    def test_process_start_command_as_a_callback_in_the_private_chat(
        self,
        mock_process_command,
        mock_remove_inline_keyboard,
    ):
        payload = copy.deepcopy(
            self.command_as_callback_in_private_chat_request_payload
        )
        payload["callback_query"]["message"]["chat"]["id"] = self.chat_id
        payload["callback_query"]["message"]["message_id"] = self.message_id
        payload["callback_query"]["data"] = "/start"

        serialized_data = self._get_serialized_request_data(payload)
        processor = BotCommandProcessor(serialized_data)
        processor.process()
        mock_process_command.assert_called_once()
        mock_remove_inline_keyboard.assert_called_once_with(
            chat_id=self.chat_id, message_id=self.message_id
        )

    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._remove_inline_keyboard_from_replied_message"
    )
    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._process_start_command"
    )
    def test_process_start_command_as_message_in_the_group(
        self,
        mock_process_command,
        mock_remove_inline_keyboard,
    ):
        serialized_data = self._get_serialized_request_data(
            self.command_as_message_in_group_request_payload
        )
        processor = BotCommandProcessor(serialized_data)
        processor.process()
        mock_process_command.assert_called_once()
        mock_remove_inline_keyboard.assert_not_called()

    # command: /instructions_confirmed
    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._remove_inline_keyboard_from_replied_message"
    )
    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._process_instructions_confirmed_command"
    )
    def test_process_instructions_confirmed_command_in_the_private_chat_as_a_message(
        self,
        mock_process_command,
        mock_remove_inline_keyboard,
    ):
        payload = copy.deepcopy(self.command_as_message_in_private_chat_request_payload)
        payload["message"]["text"] = "/instructions_confirmed"
        serialized_data = self._get_serialized_request_data(payload)
        processor = BotCommandProcessor(serialized_data)
        processor.process()
        mock_process_command.assert_called_once()
        mock_remove_inline_keyboard.assert_not_called()

    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._remove_inline_keyboard_from_replied_message"
    )
    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._process_instructions_confirmed_command"
    )
    def test_process_instructions_confirmed_command_as_a_callback_in_the_private_chat(
        self,
        mock_process_command,
        mock_remove_inline_keyboard,
    ):
        payload = copy.deepcopy(
            self.command_as_callback_in_private_chat_request_payload
        )
        payload["callback_query"]["data"] = "/instructions_confirmed"
        serialized_data = self._get_serialized_request_data(payload)
        processor = BotCommandProcessor(serialized_data)
        processor.process()
        mock_process_command.assert_called_once()
        mock_remove_inline_keyboard.assert_called_once()

    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._remove_inline_keyboard_from_replied_message"
    )
    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._process_instructions_confirmed_command"
    )
    def test_process_instructions_confirmed_command_as_message_in_the_group(
        self,
        mock_process_command,
        mock_remove_inline_keyboard,
    ):
        payload = copy.deepcopy(self.command_as_message_in_group_request_payload)
        payload["message"]["text"] = "/instructions_confirmed"
        serialized_data = self._get_serialized_request_data(payload)
        processor = BotCommandProcessor(serialized_data)
        processor.process()
        mock_process_command.assert_called_once()
        mock_remove_inline_keyboard.assert_not_called()

    # command: /input_confirmed
    @mock.patch(
        "telegram_bot.message_handling_services.SequentialMessagesProcessor.save_confirmed_data"
    )
    def test_process_input_confirmed(self, mock_save_confirmed_data):
        chat_id = 111
        telegram_user_id = 222
        telegram_user_first_name = "first_name"
        payload = copy.deepcopy(
            self.command_as_callback_in_private_chat_request_payload
        )

        payload["callback_query"]["message"]["chat"]["id"] = chat_id
        payload["callback_query"]["from"]["id"] = telegram_user_id
        payload["callback_query"]["from"]["first_name"] = telegram_user_first_name
        del payload["callback_query"]["from"]["username"]
        del payload["callback_query"]["from"]["last_name"]
        serialized_data = self._get_serialized_request_data(payload)

        parsed_message = TelegramCommandParser.parse(serialized_data)

        processor = BotCommandProcessor(telegram_message={})
        processor.parsed_telegram_message = parsed_message
        processor._process_input_confirmed_command()
        telegram_user = TelegramUser.objects.get()
        assert_that(
            telegram_user,
            has_attrs(
                telegram_id=telegram_user_id,
                username=None,
                first_name=telegram_user_first_name,
                last_name=None,
            ),
        )
        mock_save_confirmed_data.assert_called_once_with(
            user_id=telegram_user_id,
            entry_author=telegram_user,
        )

    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._remove_inline_keyboard_from_replied_message"
    )
    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._process_input_confirmed_command"
    )
    def test_process_input_confirmed_command_in_the_private_chat_as_a_message(
        self,
        mock_process_command,
        mock_remove_inline_keyboard,
    ):
        payload = copy.deepcopy(self.command_as_message_in_group_request_payload)
        payload["message"]["text"] = "/input_confirmed"
        serialized_data = self._get_serialized_request_data(payload)
        processor = BotCommandProcessor(serialized_data)
        processor.process()
        mock_process_command.assert_called_once()
        mock_remove_inline_keyboard.assert_not_called()

    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._remove_inline_keyboard_from_replied_message"
    )
    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._process_input_confirmed_command"
    )
    def test_process_input_confirmed_command_as_a_callback_in_the_private_chat(
        self,
        mock_process_command,
        mock_remove_inline_keyboard,
    ):
        payload = copy.deepcopy(
            self.command_as_callback_in_private_chat_request_payload
        )
        payload["callback_query"]["data"] = "/input_confirmed"
        serialized_data = self._get_serialized_request_data(payload)
        processor = BotCommandProcessor(serialized_data)
        processor.process()
        mock_process_command.assert_called_once()
        mock_remove_inline_keyboard.assert_called_once()

    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._remove_inline_keyboard_from_replied_message"
    )
    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._process_input_confirmed_command"
    )
    def test_process_input_confirmed_command_as_message_in_the_group(
        self,
        mock_process_command,
        mock_remove_inline_keyboard,
    ):
        payload = copy.deepcopy(self.command_as_message_in_group_request_payload)
        payload["message"]["text"] = "/input_confirmed"
        serialized_data = self._get_serialized_request_data(payload)
        processor = BotCommandProcessor(serialized_data)
        processor.process()
        mock_process_command.assert_called_once()
        mock_remove_inline_keyboard.assert_not_called()

    # command: /input_not_confirmed
    @mock.patch(
        "telegram_bot.message_handling_services.SequentialMessagesProcessor.remove_incorrect_input"
    )
    def test_process_input_not_confirmed(self, mock_remove_incorrect_input):
        user_id = "1"
        payload = copy.deepcopy(
            self.command_as_callback_in_private_chat_request_payload
        )
        payload["callback_query"]["from"]["id"] = user_id
        payload["callback_query"]["data"] = "/input_not_confirmed"
        serialized_data = self._get_serialized_request_data(payload)
        parsed_message = TelegramCommandParser.parse(payload)
        processor = BotCommandProcessor(serialized_data)
        processor.parsed_telegram_message = parsed_message
        processor._process_input_not_confirmed_command()
        mock_remove_incorrect_input.assert_called_once_with(user_id)

    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._remove_inline_keyboard_from_replied_message"
    )
    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._process_input_not_confirmed_command"
    )
    def test_process_input_not_confirmed_command_in_the_private_chat_as_a_message(
        self,
        mock_process_command,
        mock_remove_inline_keyboard,
    ):
        payload = copy.deepcopy(self.command_as_message_in_group_request_payload)
        payload["message"]["text"] = "/input_not_confirmed"
        serialized_data = self._get_serialized_request_data(payload)
        processor = BotCommandProcessor(serialized_data)
        processor.process()
        mock_process_command.assert_called_once()
        mock_remove_inline_keyboard.assert_not_called()

    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._remove_inline_keyboard_from_replied_message"
    )
    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._process_input_not_confirmed_command"
    )
    def test_process_input_not_confirmed_command_as_a_callback_in_the_private_chat(
        self,
        mock_process_command,
        mock_remove_inline_keyboard,
    ):
        payload = copy.deepcopy(
            self.command_as_callback_in_private_chat_request_payload
        )
        payload["callback_query"]["data"] = "/input_not_confirmed"
        serialized_data = self._get_serialized_request_data(payload)
        processor = BotCommandProcessor(serialized_data)
        processor.process()
        mock_process_command.assert_called_once()
        mock_remove_inline_keyboard.assert_called_once()

    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._remove_inline_keyboard_from_replied_message"
    )
    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._process_input_not_confirmed_command"
    )
    def test_process_input_not_confirmed_command_as_message_in_the_group(
        self,
        mock_process_command,
        mock_remove_inline_keyboard,
    ):
        payload = copy.deepcopy(self.command_as_message_in_group_request_payload)
        payload["message"]["text"] = "/input_not_confirmed"
        serialized_data = self._get_serialized_request_data(payload)
        processor = BotCommandProcessor(serialized_data)
        processor.process()
        mock_process_command.assert_called_once()
        mock_remove_inline_keyboard.assert_not_called()

    # command: /remove_and_restart_input
    @mock.patch(
        "telegram_bot.message_handling_services.SequentialMessagesProcessor.remove_incorrect_input"
    )
    def test_process_remove_and_restart_input(self, mock_remove_incorrect_input):
        user_id = "1"
        payload = copy.deepcopy(
            self.command_as_callback_in_private_chat_request_payload
        )
        payload["callback_query"]["from"]["id"] = user_id
        payload["callback_query"]["data"] = "/remove_and_restart_input"
        serialized_data = self._get_serialized_request_data(payload)
        parsed_message = TelegramCommandParser.parse(payload)
        processor = BotCommandProcessor(serialized_data)
        processor.parsed_telegram_message = parsed_message
        processor._process_remove_and_restart_input_command()
        mock_remove_incorrect_input.assert_called_once_with(user_id)

    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._remove_inline_keyboard_from_replied_message"
    )
    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._process_remove_and_restart_input_command"
    )
    def test_process_remove_and_restart_input_command_in_the_private_chat_as_a_message(
        self,
        mock_process_command,
        mock_remove_inline_keyboard,
    ):
        payload = copy.deepcopy(self.command_as_message_in_group_request_payload)
        payload["message"]["text"] = "/remove_and_restart_input"
        serialized_data = self._get_serialized_request_data(payload)
        processor = BotCommandProcessor(serialized_data)
        processor.process()
        mock_process_command.assert_called_once()
        mock_remove_inline_keyboard.assert_not_called()

    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._remove_inline_keyboard_from_replied_message"
    )
    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._process_remove_and_restart_input_command"
    )
    def test_process_remove_and_restart_input_command_as_a_callback_in_the_private_chat(
        self,
        mock_process_command,
        mock_remove_inline_keyboard,
    ):
        payload = copy.deepcopy(
            self.command_as_callback_in_private_chat_request_payload
        )
        payload["callback_query"]["data"] = "/remove_and_restart_input"
        serialized_data = self._get_serialized_request_data(payload)
        processor = BotCommandProcessor(serialized_data)
        processor.process()
        mock_process_command.assert_called_once()
        mock_remove_inline_keyboard.assert_called_once()

    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._remove_inline_keyboard_from_replied_message"
    )
    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._process_remove_and_restart_input_command"
    )
    def test_process_remove_and_restart_input_command_as_message_in_the_group(
        self,
        mock_process_command,
        mock_remove_inline_keyboard,
    ):
        payload = copy.deepcopy(self.command_as_message_in_group_request_payload)
        payload["message"]["text"] = "/remove_and_restart_input"
        serialized_data = self._get_serialized_request_data(payload)
        processor = BotCommandProcessor(serialized_data)
        processor.process()
        mock_process_command.assert_called_once()
        mock_remove_inline_keyboard.assert_not_called()

    # command: /continue_input
    def test_process_continue_input(self):
        user_id = "1"
        payload = copy.deepcopy(
            self.command_as_callback_in_private_chat_request_payload
        )
        payload["callback_query"]["from"]["id"] = user_id
        payload["callback_query"]["data"] = "/continue_input"
        serialized_data = self._get_serialized_request_data(payload)
        parsed_message = TelegramCommandParser.parse(payload)
        processor = BotCommandProcessor(serialized_data)
        processor.parsed_telegram_message = parsed_message
        assert processor._process_continue_input_command() is None

    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._remove_inline_keyboard_from_replied_message"
    )
    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._process_continue_input_command"
    )
    def test_process_continue_input_command_in_the_private_chat_as_a_message(
        self,
        mock_process_command,
        mock_remove_inline_keyboard,
    ):
        payload = copy.deepcopy(self.command_as_message_in_group_request_payload)
        payload["message"]["text"] = "/continue_input"
        serialized_data = self._get_serialized_request_data(payload)
        processor = BotCommandProcessor(serialized_data)
        processor.process()
        mock_process_command.assert_called_once()
        mock_remove_inline_keyboard.assert_not_called()

    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._remove_inline_keyboard_from_replied_message"
    )
    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._process_continue_input_command"
    )
    def test_process_continue_input_command_as_a_callback_in_the_private_chat(
        self,
        mock_process_command,
        mock_remove_inline_keyboard,
    ):
        payload = copy.deepcopy(
            self.command_as_callback_in_private_chat_request_payload
        )
        payload["callback_query"]["data"] = "/continue_input"
        serialized_data = self._get_serialized_request_data(payload)
        processor = BotCommandProcessor(serialized_data)
        processor.process()
        mock_process_command.assert_called_once()
        mock_remove_inline_keyboard.assert_called_once()

    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._remove_inline_keyboard_from_replied_message"
    )
    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._process_continue_input_command"
    )
    def test_process_continue_input_command_as_message_in_the_group(
        self,
        mock_process_command,
        mock_remove_inline_keyboard,
    ):
        payload = copy.deepcopy(self.command_as_message_in_group_request_payload)
        payload["message"]["text"] = "/continue_input"
        serialized_data = self._get_serialized_request_data(payload)
        processor = BotCommandProcessor(serialized_data)
        processor.process()
        mock_process_command.assert_called_once()
        mock_remove_inline_keyboard.assert_not_called()

    # command: /report_
    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._remove_inline_keyboard_from_replied_message"
    )
    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._process_report_generation_command"
    )
    def test_process_report_command_in_the_private_chat_as_a_message(
        self,
        mock_process_command,
        mock_remove_inline_keyboard,
    ):
        payload = copy.deepcopy(self.command_as_message_in_private_chat_request_payload)
        payload["message"]["text"] = "/report_01-01-2024_02-01-2024"
        serialized_data = self._get_serialized_request_data(payload)
        processor = BotCommandProcessor(serialized_data)
        processor.process()
        mock_process_command.assert_called_once()
        mock_remove_inline_keyboard.assert_not_called()

    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._remove_inline_keyboard_from_replied_message"
    )
    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._process_report_generation_command"
    )
    def test_process_report_command_as_a_callback_in_the_private_chat(
        self,
        mock_process_command,
        mock_remove_inline_keyboard,
    ):
        payload = copy.deepcopy(
            self.command_as_callback_in_private_chat_request_payload
        )
        payload["callback_query"]["data"] = "/report_01-01-2024_02-01-2024"
        serialized_data = self._get_serialized_request_data(payload)
        processor = BotCommandProcessor(serialized_data)
        processor.process()
        mock_process_command.assert_called_once()
        mock_remove_inline_keyboard.assert_called_once()

    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._remove_inline_keyboard_from_replied_message"
    )
    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._process_report_generation_command"
    )
    def test_process_report_command_as_message_in_the_group(
        self,
        mock_process_command,
        mock_remove_inline_keyboard,
    ):
        payload = copy.deepcopy(self.command_as_message_in_group_request_payload)
        payload["message"]["text"] = "/report_01-01-2024_02-01-2024"
        serialized_data = self._get_serialized_request_data(payload)
        processor = BotCommandProcessor(serialized_data)
        processor.process()
        mock_process_command.assert_called_once()
        mock_remove_inline_keyboard.assert_not_called()

    @override_settings(ADMIN_USER_IDS=[123])
    def test_process_report_user_not_an_admin(self):
        payload = copy.deepcopy(self.command_as_message_in_private_chat_request_payload)
        payload["message"]["text"] = "/report_01-01-2024_02-01-2024"
        serialized_data = self._get_serialized_request_data(payload)
        processor = BotCommandProcessor(serialized_data)
        with self.assertRaises(UnauthorizedUserCalledReportGenerationException):
            processor.process()

    @override_settings(ADMIN_USER_IDS=[])
    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._process_report_generation_command"
    )
    def test_process_report_admin_ids_is_empty(self, mock_process_command):
        payload = copy.deepcopy(self.command_as_message_in_private_chat_request_payload)
        payload["message"]["text"] = "/report_01-01-2024_02-01-2024"
        serialized_data = self._get_serialized_request_data(payload)
        processor = BotCommandProcessor(serialized_data)
        processor.process()
        mock_process_command.assert_called_once()

    # command: /unknown
    def test_process_unknown_command_in_the_private_chat_as_a_message(self):
        with self.assertRaises(UnknownCommandException):
            payload = copy.deepcopy(
                self.command_as_message_in_private_chat_request_payload
            )
            payload["message"]["text"] = "/unknown_command"
            serialized_data = self._get_serialized_request_data(payload)
            processor = BotCommandProcessor(serialized_data)
            processor.process()

    @mock.patch("telegram_bot.message_handling_services.requests.post")
    def test_process_unknown_command_as_a_callback_in_the_private_chat(self, mock_post):
        with self.assertRaises(UnknownCommandException):
            payload = copy.deepcopy(
                self.command_as_callback_in_private_chat_request_payload
            )
            payload["callback_query"]["data"] = "/unknown_command"
            serialized_data = self._get_serialized_request_data(payload)
            processor = BotCommandProcessor(serialized_data)
            processor.process()

    def test_process_unknown_command_as_message_in_the_group(self):
        with self.assertRaises(UnknownCommandException):
            payload = copy.deepcopy(self.command_as_message_in_group_request_payload)
            payload["message"]["text"] = "/unknown_command"
            serialized_data = self._get_serialized_request_data(payload)
            processor = BotCommandProcessor(serialized_data)
            processor.process()

    # prepare_response method

    # command: /start
    def test_get_start_command_response(self):
        payload = copy.deepcopy(self.command_as_message_in_private_chat_request_payload)
        payload["message"]["text"] = "/start"
        serialized_data = self._get_serialized_request_data(payload)
        parsed_message = TelegramCommandParser.parse(serialized_data)
        processor = BotCommandProcessor(serialized_data)
        processor.parsed_telegram_message = parsed_message
        response = processor._get_start_command_response()
        assert_that(
            response,
            is_mapping(
                {
                    "data": is_mapping(
                        {
                            "text": FIRST_INSTRUCTIONS,
                            "chat_id": payload["message"]["chat"]["id"],
                            "reply_markup": json.dumps(
                                {
                                    "inline_keyboard": [
                                        [
                                            {
                                                "text": "Зрозуміло, починаємо",
                                                "callback_data": "/instructions_confirmed",
                                            }
                                        ]
                                    ],
                                }
                            ),
                        }
                    )
                }
            ),
        )

    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._get_start_command_response"
    )
    def test_prepare_response_start_command_in_the_private_chat_as_a_message(
        self, mock_get_response
    ):
        payload = copy.deepcopy(self.command_as_message_in_private_chat_request_payload)
        payload["message"]["text"] = "/start"
        serialized_data = self._get_serialized_request_data(payload)
        parsed_message = TelegramCommandParser.parse(serialized_data)
        processor = BotCommandProcessor(serialized_data)
        processor.parsed_telegram_message = parsed_message
        processor.prepare_response()
        mock_get_response.assert_called_once()

    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._get_start_command_response"
    )
    def test_prepare_response_start_command_as_a_callback_in_the_private_chat(
        self, mock_get_response
    ):
        payload = copy.deepcopy(
            self.command_as_callback_in_private_chat_request_payload
        )
        payload["callback_query"]["data"] = "/start"
        serialized_data = self._get_serialized_request_data(payload)
        parsed_message = TelegramCommandParser.parse(serialized_data)
        processor = BotCommandProcessor(serialized_data)
        processor.parsed_telegram_message = parsed_message
        processor.prepare_response()
        mock_get_response.assert_called_once()

    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._get_start_command_response"
    )
    def test_prepare_response_start_command_as_message_in_the_group(
        self, mock_get_response
    ):
        payload = copy.deepcopy(self.command_as_message_in_group_request_payload)
        payload["message"]["text"] = "/start"
        serialized_data = self._get_serialized_request_data(payload)
        parsed_message = TelegramCommandParser.parse(serialized_data)
        processor = BotCommandProcessor(serialized_data)
        processor.parsed_telegram_message = parsed_message
        processor.prepare_response()
        mock_get_response.assert_not_called()

    # command: /instructions_confirmed
    def test_get_instructions_confirmed_command_response(self):
        payload = copy.deepcopy(self.command_as_message_in_private_chat_request_payload)
        payload["message"]["text"] = "/instructions_confirmed"
        serialized_data = self._get_serialized_request_data(payload)
        parsed_message = TelegramCommandParser.parse(serialized_data)
        processor = BotCommandProcessor(serialized_data)
        processor.parsed_telegram_message = parsed_message
        response = processor._get_instructions_confirmed_command_response()
        assert_that(
            response,
            is_mapping(
                {
                    "data": is_mapping(
                        {
                            "text": INQUERY_MESSAGE_START + CASE_ID_INQUERY,
                            "chat_id": payload["message"]["chat"]["id"],
                        }
                    )
                }
            ),
        )

    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._get_instructions_confirmed_command_response"
    )
    def test_prepare_response_instructions_confirmed_command_in_the_private_chat_as_a_message(
        self, mock_get_response
    ):
        payload = copy.deepcopy(self.command_as_message_in_private_chat_request_payload)
        payload["message"]["text"] = "/instructions_confirmed"
        serialized_data = self._get_serialized_request_data(payload)
        parsed_message = TelegramCommandParser.parse(serialized_data)
        processor = BotCommandProcessor(serialized_data)
        processor.parsed_telegram_message = parsed_message
        processor.prepare_response()
        mock_get_response.assert_called_once()

    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._get_instructions_confirmed_command_response"
    )
    def test_prepare_response_instructions_confirmed_command_as_a_callback_in_the_private_chat(
        self, mock_get_response
    ):
        payload = copy.deepcopy(
            self.command_as_callback_in_private_chat_request_payload
        )
        payload["callback_query"]["data"] = "/instructions_confirmed"
        serialized_data = self._get_serialized_request_data(payload)
        parsed_message = TelegramCommandParser.parse(serialized_data)
        processor = BotCommandProcessor(serialized_data)
        processor.parsed_telegram_message = parsed_message
        processor.prepare_response()
        mock_get_response.assert_called_once()

    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._get_instructions_confirmed_command_response"
    )
    def test_prepare_response_instructions_confirmed_command_as_message_in_the_group(
        self, mock_get_response
    ):
        payload = copy.deepcopy(self.command_as_message_in_group_request_payload)
        payload["message"]["text"] = "/instructions_confirmed"
        serialized_data = self._get_serialized_request_data(payload)
        parsed_message = TelegramCommandParser.parse(serialized_data)
        processor = BotCommandProcessor(serialized_data)
        processor.parsed_telegram_message = parsed_message
        processor.prepare_response()
        mock_get_response.assert_not_called()

    # command: /input_confirmed
    def test_get_input_confirmed_command_response(self):
        payload = copy.deepcopy(self.command_as_message_in_private_chat_request_payload)
        payload["message"]["text"] = "/input_confirmed"
        serialized_data = self._get_serialized_request_data(payload)
        parsed_message = TelegramCommandParser.parse(serialized_data)
        processor = BotCommandProcessor(serialized_data)
        processor.parsed_telegram_message = parsed_message
        response = processor._get_input_confirmed_command_response()
        assert_that(
            response,
            is_mapping(
                {
                    "data": is_mapping(
                        {
                            "text": INPUT_CONFIRMED_RESPONSE,
                            "chat_id": payload["message"]["chat"]["id"],
                        }
                    )
                }
            ),
        )

    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._get_input_confirmed_command_response"
    )
    def test_prepare_response_input_confirmed_command_in_the_private_chat_as_a_message(
        self, mock_get_response
    ):
        payload = copy.deepcopy(self.command_as_message_in_private_chat_request_payload)
        payload["message"]["text"] = "/input_confirmed"
        serialized_data = self._get_serialized_request_data(payload)
        parsed_message = TelegramCommandParser.parse(serialized_data)
        processor = BotCommandProcessor(serialized_data)
        processor.parsed_telegram_message = parsed_message
        processor.prepare_response()
        mock_get_response.assert_called_once()

    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._get_input_confirmed_command_response"
    )
    def test_prepare_response_input_confirmed_command_as_a_callback_in_the_private_chat(
        self, mock_get_response
    ):
        payload = copy.deepcopy(
            self.command_as_callback_in_private_chat_request_payload
        )
        payload["callback_query"]["data"] = "/input_confirmed"
        serialized_data = self._get_serialized_request_data(payload)
        parsed_message = TelegramCommandParser.parse(serialized_data)
        processor = BotCommandProcessor(serialized_data)
        processor.parsed_telegram_message = parsed_message
        processor.prepare_response()
        mock_get_response.assert_called_once()

    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._get_input_confirmed_command_response"
    )
    def test_prepare_response_input_confirmed_command_as_message_in_the_group(
        self, mock_get_response
    ):
        payload = copy.deepcopy(self.command_as_message_in_group_request_payload)
        payload["message"]["text"] = "/input_confirmed"
        serialized_data = self._get_serialized_request_data(payload)
        parsed_message = TelegramCommandParser.parse(serialized_data)
        processor = BotCommandProcessor(serialized_data)
        processor.parsed_telegram_message = parsed_message
        processor.prepare_response()
        mock_get_response.assert_not_called()

    # command: /input_not_confirmed
    def test_get_input_not_confirmed_command_response(self):
        payload = copy.deepcopy(self.command_as_message_in_private_chat_request_payload)
        payload["message"]["text"] = "/input_not_confirmed"
        serialized_data = self._get_serialized_request_data(payload)
        parsed_message = TelegramCommandParser.parse(serialized_data)
        processor = BotCommandProcessor(serialized_data)
        processor.parsed_telegram_message = parsed_message
        response = processor._get_input_not_confirmed_command_response()
        assert_that(
            response,
            is_mapping(
                {
                    "data": is_mapping(
                        {
                            "text": INPUT_NOT_CONFIRMED_RESPONSE,
                            "chat_id": payload["message"]["chat"]["id"],
                            "reply_markup": json.dumps(
                                {
                                    "inline_keyboard": [
                                        [
                                            {
                                                "text": "Зрозуміло, починаємо",
                                                "callback_data": "/instructions_confirmed",
                                            }
                                        ]
                                    ],
                                }
                            ),
                        }
                    )
                }
            ),
        )

    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._get_input_not_confirmed_command_response"
    )
    def test_prepare_response_input_not_confirmed_command_in_the_private_chat_as_a_message(
        self, mock_get_response
    ):
        payload = copy.deepcopy(self.command_as_message_in_private_chat_request_payload)
        payload["message"]["text"] = "/input_not_confirmed"
        serialized_data = self._get_serialized_request_data(payload)
        parsed_message = TelegramCommandParser.parse(serialized_data)
        processor = BotCommandProcessor(serialized_data)
        processor.parsed_telegram_message = parsed_message
        processor.prepare_response()
        mock_get_response.assert_called_once()

    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._get_input_not_confirmed_command_response"
    )
    def test_prepare_response_input_not_confirmed_command_as_a_callback_in_the_private_chat(
        self, mock_get_response
    ):
        payload = copy.deepcopy(
            self.command_as_callback_in_private_chat_request_payload
        )
        payload["callback_query"]["data"] = "/input_not_confirmed"
        serialized_data = self._get_serialized_request_data(payload)
        parsed_message = TelegramCommandParser.parse(serialized_data)
        processor = BotCommandProcessor(serialized_data)
        processor.parsed_telegram_message = parsed_message
        processor.prepare_response()
        mock_get_response.assert_called_once()

    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._get_input_not_confirmed_command_response"
    )
    def test_prepare_response_input_not_confirmed_command_as_message_in_the_group(
        self, mock_get_response
    ):
        payload = copy.deepcopy(self.command_as_message_in_group_request_payload)
        payload["message"]["text"] = "/input_not_confirmed"
        serialized_data = self._get_serialized_request_data(payload)
        parsed_message = TelegramCommandParser.parse(serialized_data)
        processor = BotCommandProcessor(serialized_data)
        processor.parsed_telegram_message = parsed_message
        processor.prepare_response()
        mock_get_response.assert_not_called()

    # command: /remove_and_restart_input
    def test_get_remove_and_restart_input_command_response(self):
        payload = copy.deepcopy(self.command_as_message_in_private_chat_request_payload)
        payload["message"]["text"] = "/remove_and_restart_input"
        serialized_data = self._get_serialized_request_data(payload)
        parsed_message = TelegramCommandParser.parse(serialized_data)
        processor = BotCommandProcessor(serialized_data)
        processor.parsed_telegram_message = parsed_message
        response = processor._get_remove_and_restart_input_command_response()
        assert_that(
            response,
            is_mapping(
                {
                    "data": is_mapping(
                        {
                            "text": INQUERY_MESSAGE_START + CASE_ID_INQUERY,
                            "chat_id": payload["message"]["chat"]["id"],
                        }
                    )
                }
            ),
        )

    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._get_remove_and_restart_input_command_response"
    )
    def test_prepare_response_remove_and_restart_input_command_in_the_private_chat_as_a_message(
        self, mock_get_response
    ):
        payload = copy.deepcopy(self.command_as_message_in_private_chat_request_payload)
        payload["message"]["text"] = "/remove_and_restart_input"
        serialized_data = self._get_serialized_request_data(payload)
        parsed_message = TelegramCommandParser.parse(serialized_data)
        processor = BotCommandProcessor(serialized_data)
        processor.parsed_telegram_message = parsed_message
        processor.prepare_response()
        mock_get_response.assert_called_once()

    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._get_remove_and_restart_input_command_response"
    )
    def test_prepare_response_remove_and_restart_input_command_as_a_callback_in_the_private_chat(
        self, mock_get_response
    ):
        payload = copy.deepcopy(
            self.command_as_callback_in_private_chat_request_payload
        )
        payload["callback_query"]["data"] = "/remove_and_restart_input"
        serialized_data = self._get_serialized_request_data(payload)
        parsed_message = TelegramCommandParser.parse(serialized_data)
        processor = BotCommandProcessor(serialized_data)
        processor.parsed_telegram_message = parsed_message
        processor.prepare_response()
        mock_get_response.assert_called_once()

    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._get_remove_and_restart_input_command_response"
    )
    def test_prepare_response_remove_and_restart_input_command_as_message_in_the_group(
        self, mock_get_response
    ):
        payload = copy.deepcopy(self.command_as_message_in_group_request_payload)
        payload["message"]["text"] = "/remove_and_restart_input"
        serialized_data = self._get_serialized_request_data(payload)
        parsed_message = TelegramCommandParser.parse(serialized_data)
        processor = BotCommandProcessor(serialized_data)
        processor.parsed_telegram_message = parsed_message
        processor.prepare_response()
        mock_get_response.assert_not_called()

    # command: /continue_input
    @mock.patch("telegram_bot.sequential_messages_processor.client")
    @mock.patch(
        "telegram_bot.message_handling_services.SequentialMessagesProcessor.get_response_text"
    )
    def test_get_continue_input_command_response(
        self, mock_get_response_text, redis_mock
    ):
        redis_mock.hgetall.return_value = {b"case_id": "1"}
        mock_get_response_text.return_value = MESSAGES_MAPPING["hero_last_name"]
        payload = copy.deepcopy(self.command_as_message_in_private_chat_request_payload)
        payload["message"]["text"] = "/continue_input"
        serialized_data = self._get_serialized_request_data(payload)
        parsed_message = TelegramCommandParser.parse(serialized_data)
        processor = BotCommandProcessor(serialized_data)
        processor.parsed_telegram_message = parsed_message
        response = processor._get_continue_input_command_response()
        assert_that(
            response,
            is_mapping(
                {
                    "data": is_mapping(
                        {
                            "text": MESSAGES_MAPPING["hero_last_name"],
                            "chat_id": payload["message"]["chat"]["id"],
                        }
                    )
                }
            ),
        )

    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._get_continue_input_command_response"
    )
    def test_prepare_response_continue_input_command_in_the_private_chat_as_a_message(
        self, mock_get_response
    ):
        payload = copy.deepcopy(self.command_as_message_in_private_chat_request_payload)
        payload["message"]["text"] = "/continue_input"
        serialized_data = self._get_serialized_request_data(payload)
        parsed_message = TelegramCommandParser.parse(serialized_data)
        processor = BotCommandProcessor(serialized_data)
        processor.parsed_telegram_message = parsed_message
        processor.prepare_response()
        mock_get_response.assert_called_once()

    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._get_continue_input_command_response"
    )
    def test_prepare_response_continue_input_command_as_a_callback_in_the_private_chat(
        self, mock_get_response
    ):
        payload = copy.deepcopy(
            self.command_as_callback_in_private_chat_request_payload
        )
        payload["callback_query"]["data"] = "/continue_input"
        serialized_data = self._get_serialized_request_data(payload)
        parsed_message = TelegramCommandParser.parse(serialized_data)
        processor = BotCommandProcessor(serialized_data)
        processor.parsed_telegram_message = parsed_message
        processor.prepare_response()
        mock_get_response.assert_called_once()

    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._get_continue_input_command_response"
    )
    def test_prepare_response_continue_input_command_as_message_in_the_group(
        self, mock_get_response
    ):
        payload = copy.deepcopy(self.command_as_message_in_group_request_payload)
        payload["message"]["text"] = "/continue_input"
        serialized_data = self._get_serialized_request_data(payload)
        parsed_message = TelegramCommandParser.parse(serialized_data)
        processor = BotCommandProcessor(serialized_data)
        processor.parsed_telegram_message = parsed_message
        processor.prepare_response()
        mock_get_response.assert_not_called()

    # command: /unknown
    def test_prepare_response_unknown_command_in_the_private_chat_as_a_message(self):
        payload = copy.deepcopy(self.command_as_message_in_private_chat_request_payload)
        payload["message"]["text"] = "/unknown_command"
        serialized_data = self._get_serialized_request_data(payload)
        parsed_message = TelegramCommandParser.parse(serialized_data)
        processor = BotCommandProcessor(serialized_data)
        processor.parsed_telegram_message = parsed_message
        with self.assertRaises(UnknownCommandException):
            processor.prepare_response()

    def test_prepare_response_unknown_command_as_a_callback_in_the_private_chat(
        self,
    ):
        payload = copy.deepcopy(
            self.command_as_callback_in_private_chat_request_payload
        )
        payload["callback_query"]["data"] = "/unknown_command"
        serialized_data = self._get_serialized_request_data(payload)
        parsed_message = TelegramCommandParser.parse(serialized_data)
        processor = BotCommandProcessor(serialized_data)
        processor.parsed_telegram_message = parsed_message
        with self.assertRaises(UnknownCommandException):
            processor.prepare_response()

    def test_prepare_response_inknown_command_as_message_in_the_group(self):
        payload = copy.deepcopy(self.command_as_message_in_group_request_payload)
        payload["message"]["text"] = "/unknown_command"
        serialized_data = self._get_serialized_request_data(payload)
        parsed_message = TelegramCommandParser.parse(serialized_data)
        processor = BotCommandProcessor(serialized_data)
        processor.parsed_telegram_message = parsed_message
        response = processor.prepare_response()
        assert response is None

    # command: /report_
    def test_get_report_command_response(self):
        payload = copy.deepcopy(self.command_as_message_in_private_chat_request_payload)
        payload["message"]["text"] = "/report_01-02-2024_04-02-2024"
        serialized_data = self._get_serialized_request_data(payload)
        parsed_message = TelegramCommandParser.parse(serialized_data)
        processor = BotCommandProcessor(serialized_data)
        processor.parsed_telegram_message = parsed_message
        processor._process_report_generation_command()
        response = processor._get_report_generation_command_response()
        try:
            assert_that(
                response,
                is_mapping(
                    {
                        "data": is_mapping(
                            {
                                "text": "",
                                "chat_id": payload["message"]["chat"]["id"],
                            }
                        ),
                        "files": is_mapping(
                            {"document": has_attrs(name=processor.generated_report)}
                        ),
                    }
                ),
            )
        except Exception:
            raise
        finally:
            os.remove(processor.generated_report)

    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._get_report_generation_command_response"
    )
    def test_prepare_response_report_command_in_the_private_chat_as_a_message(
        self, mock_get_response
    ):
        payload = copy.deepcopy(self.command_as_message_in_private_chat_request_payload)
        payload["message"]["text"] = "/report_01-02-2024_02-03-2024"
        serialized_data = self._get_serialized_request_data(payload)
        parsed_message = TelegramCommandParser.parse(serialized_data)
        processor = BotCommandProcessor(serialized_data)
        processor.parsed_telegram_message = parsed_message
        processor.prepare_response()
        mock_get_response.assert_called_once()

    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._get_report_generation_command_response"
    )
    def test_prepare_response_report_command_as_a_callback_in_the_private_chat(
        self, mock_get_response
    ):
        payload = copy.deepcopy(
            self.command_as_callback_in_private_chat_request_payload
        )
        payload["callback_query"]["data"] = "/report_01-02-2024_02-03-2024"
        serialized_data = self._get_serialized_request_data(payload)
        parsed_message = TelegramCommandParser.parse(serialized_data)
        processor = BotCommandProcessor(serialized_data)
        processor.parsed_telegram_message = parsed_message
        processor.prepare_response()
        mock_get_response.assert_called_once()

    @mock.patch(
        "telegram_bot.message_handling_services.BotCommandProcessor._get_report_generation_command_response"
    )
    def test_prepare_response_report_command_as_message_in_the_group(
        self, mock_get_response
    ):
        payload = copy.deepcopy(self.command_as_message_in_group_request_payload)
        payload["message"]["text"] = "/report_01-02-2024_02-03-2024"
        serialized_data = self._get_serialized_request_data(payload)
        parsed_message = TelegramCommandParser.parse(serialized_data)
        processor = BotCommandProcessor(serialized_data)
        processor.parsed_telegram_message = parsed_message
        processor.prepare_response()
        mock_get_response.assert_not_called()
