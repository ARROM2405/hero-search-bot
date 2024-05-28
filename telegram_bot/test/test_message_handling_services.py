import copy
import json
from unittest import mock

from precisely import assert_that, has_attrs, is_mapping

from telegram_bot.constants import ORDER_OF_MESSAGES, MESSAGES_MAPPING
from telegram_bot.enums import ChatType, UserActionType
from telegram_bot.exceptions import TelegramMessageNotParsedException
from telegram_bot.message_handling_services import (
    MessageHandler,
    MemberStatusChangeProcessor,
    BotCommandProcessor,
    UserMessageProcessor,
)
from telegram_bot.messages_texts import FIRST_INSTRUCTIONS, ALL_DATA_RECEIVED_RESPONSE
from telegram_bot.models import BotStatusChange, TelegramUser
from telegram_bot.parsers import UserMessageParser
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
    @mock.patch("telegram_bot.message_handling_services.requests.post")
    def test_handle_telegram_user_message_in_private_chat(
        self,
        post_request_mock,
        get_response_text_mock,
    ):
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
        assert mock_called_with_kwargs["reply_markup"] is None


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
                "telegram_bot.sequential_messages_processor.redis.Redis.expire"
            ) as expire_mock:
                hgetall_mock.return_value = {}
                serialized_request_data = self._get_serialized_request_data(payload)
                processor = UserMessageProcessor(serialized_request_data)
                processor.process()
                hgetall_mock.assert_called_once()
                hset_mock.assert_called_once_with(
                    chat_id, mapping={"case_id": message_text}
                )
                expire_mock.assert_called_once_with(chat_id, 30 * 60)
                assert processor.all_data_received is False

        with self.subTest():
            with mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hgetall",
            ) as hgetall_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hset"
            ) as hset_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.expire"
            ) as expire_mock:
                hgetall_mock.return_value = {"case_id".encode(): None}
                serialized_request_data = self._get_serialized_request_data(payload)
                processor = UserMessageProcessor(serialized_request_data)
                processor.process()
                hgetall_mock.assert_called_once()
                hset_mock.assert_called_once_with(
                    chat_id, mapping={"hero_last_name": message_text}
                )
                expire_mock.assert_not_called()
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

    def test_prepare_response_user_message_in_private_chat(self):
        chat_id = self.message_in_private_chat_request_payload["message"]["chat"]["id"]
        payload = copy.deepcopy(self.message_in_private_chat_request_payload)
        del payload["message"]["from"]["first_name"]
        del payload["message"]["from"]["last_name"]

        with self.subTest():
            with mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hgetall",
            ) as hgetall_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hset"
            ) as hset_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.expire"
            ) as expire_mock:
                hgetall_mock.return_value = {}
                serialized_request_data = self._get_serialized_request_data(payload)
                processor = UserMessageProcessor(serialized_request_data)
                processor.process()
                response_object = processor.prepare_response()
                assert_that(
                    response_object,
                    is_mapping(
                        {
                            "text": MESSAGES_MAPPING["hero_last_name"],
                            "chat_id": chat_id,
                            "reply_markup": None,
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
                            "text": MESSAGES_MAPPING["hero_patronymic"],
                            "chat_id": chat_id,
                            "reply_markup": None,
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
                            "text": ALL_DATA_RECEIVED_RESPONSE,
                            "chat_id": chat_id,
                            "reply_markup": None,
                        }
                    ),
                )
