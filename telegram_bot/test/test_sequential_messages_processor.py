from unittest import mock

from telegram_bot.exceptions import (
    AllDataReceivedException,
    UserMessageValidationFailedException,
)
from telegram_bot.sequential_messages_processor import SequentialMessagesProcessor
from telegram_bot.test.base import TelegramBotRequestsTestBase


class TestSequentialMessagesProcessor(TelegramBotRequestsTestBase):

    @mock.patch("telegram_bot.sequential_messages_processor.client")
    def test_get_current_and_next_message_keys(self, redis_mock):
        message_data = "some_message_data"
        chat_id = "123123"
        with self.subTest():
            redis_mock.hgetall.return_value = {}
            processor = SequentialMessagesProcessor(
                message_data=message_data,
                user_id=chat_id,
            )
            assert (
                processor.current_message_key,
                processor.next_message_key,
            ) == (
                "case_id",
                "hero_last_name",
            )
        with self.subTest():
            redis_mock.hgetall.return_value = {b"case_id": "123123"}
            processor = SequentialMessagesProcessor(
                message_data=message_data,
                user_id=chat_id,
            )
            assert (
                processor.current_message_key,
                processor.next_message_key,
            ) == (
                "hero_last_name",
                "hero_first_name",
            )
        with self.subTest():
            redis_mock.hgetall.return_value = {
                b"case_id": "123123",
                b"hero_last_name": "AAA",
                b"hero_first_name": "BBB",
                b"hero_patronymic": "CCC",
                b"hero_date_of_birth": "01/01/1990",
                b"item_used_for_dna_extraction": "DDD",
                b"relative_last_name": "EEE",
                b"relative_first_name": "FFF",
                b"relative_patronymic": "GGG",
            }
            processor = SequentialMessagesProcessor(
                message_data=message_data,
                user_id=chat_id,
            )
            assert (
                processor.current_message_key,
                processor.next_message_key,
            ) == (
                "is_added_to_dna_db",
                "comment",
            )
        with self.subTest():
            redis_mock.hgetall.return_value = {
                b"case_id": "123123",
                b"hero_last_name": "AAA",
                b"hero_first_name": "BBB",
                b"hero_patronymic": "CCC",
                b"hero_date_of_birth": "01/01/1990",
                b"item_used_for_dna_extraction": "DDD",
                b"relative_last_name": "EEE",
                b"relative_first_name": "FFF",
                b"relative_patronymic": "GGG",
                b"is_added_to_dna_db": "HHH",
            }
            processor = SequentialMessagesProcessor(
                message_data=message_data,
                user_id=chat_id,
            )
            assert (
                processor.current_message_key,
                processor.next_message_key,
            ) == (
                "comment",
                None,
            )

    def test_save_message(self):
        chat_id = self.message_in_private_chat_request_payload["message"]["chat"]["id"]
        message_text = self.message_in_private_chat_request_payload["message"]["text"]

        def process_sequential_message(
            message_text_param: str = None,
            chat_id_param: int = None,
        ):
            processor = SequentialMessagesProcessor(
                message_text_param or message_text,
                chat_id_param or chat_id,
            )
            processor.save_message()

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
                process_sequential_message()
                hgetall_mock.assert_called_once()
                hset_mock.assert_called_once_with(
                    str(chat_id), mapping={"case_id": message_text}
                )

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
                process_sequential_message()
                hgetall_mock.assert_called_once()
                hset_mock.assert_called_once_with(
                    str(chat_id), mapping={"hero_last_name": message_text}
                )

        with self.subTest():
            with mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hgetall",
            ) as hgetall_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hset"
            ) as hset_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.SequentialMessagesProcessor.check_if_user_input_exists"
            ) as check_if_user_input_exists_mock:
                check_if_user_input_exists_mock.return_value = True
                hgetall_mock.return_value = {
                    "case_id".encode(): None,
                    "hero_last_name".encode(): None,
                }
                process_sequential_message()
                hgetall_mock.assert_called_once()
                hset_mock.assert_called_once_with(
                    str(chat_id), mapping={"hero_first_name": message_text}
                )

        with self.subTest():
            with mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hgetall",
            ) as hgetall_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hset"
            ) as hset_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.SequentialMessagesProcessor.check_if_user_input_exists"
            ) as check_if_user_input_exists_mock:
                check_if_user_input_exists_mock.return_value = True
                hgetall_mock.return_value = {
                    "case_id".encode(): None,
                    "hero_last_name".encode(): None,
                    "hero_first_name".encode(): None,
                }
                process_sequential_message()
                hgetall_mock.assert_called_once()
                hset_mock.assert_called_once_with(
                    str(chat_id), mapping={"hero_patronymic": message_text}
                )

        with self.subTest():
            # date validation passed
            with mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hgetall",
            ) as hgetall_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hset"
            ) as hset_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.SequentialMessagesProcessor.check_if_user_input_exists"
            ) as check_if_user_input_exists_mock:
                check_if_user_input_exists_mock.return_value = True
                hgetall_mock.return_value = {
                    "case_id".encode(): None,
                    "hero_last_name".encode(): None,
                    "hero_first_name".encode(): None,
                    "hero_patronymic".encode(): None,
                }
                date_message_input = "01/01/2000"
                process_sequential_message(message_text_param=date_message_input)
                hgetall_mock.assert_called_once()
                hset_mock.assert_called_once_with(
                    str(chat_id), mapping={"hero_date_of_birth": date_message_input}
                )

        with self.subTest():
            # date validation not passed
            with mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hgetall",
            ) as hgetall_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hset"
            ) as hset_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.SequentialMessagesProcessor.check_if_user_input_exists"
            ) as check_if_user_input_exists_mock:
                with self.assertRaises(UserMessageValidationFailedException):
                    check_if_user_input_exists_mock.return_value = True
                    hgetall_mock.return_value = {
                        "case_id".encode(): None,
                        "hero_last_name".encode(): None,
                        "hero_first_name".encode(): None,
                        "hero_patronymic".encode(): None,
                    }
                    process_sequential_message()
                    hgetall_mock.assert_called_once()
                    hset_mock.assert_not_called()

        with self.subTest():
            with mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hgetall",
            ) as hgetall_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hset"
            ) as hset_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.SequentialMessagesProcessor.check_if_user_input_exists"
            ) as check_if_user_input_exists_mock:
                check_if_user_input_exists_mock.return_value = True
                hgetall_mock.return_value = {
                    "case_id".encode(): None,
                    "hero_last_name".encode(): None,
                    "hero_first_name".encode(): None,
                    "hero_patronymic".encode(): None,
                    "hero_date_of_birth".encode(): None,
                }
                process_sequential_message()
                hgetall_mock.assert_called_once()
                hset_mock.assert_called_once_with(
                    str(chat_id), mapping={"item_used_for_dna_extraction": message_text}
                )

        with self.subTest():
            with mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hgetall",
            ) as hgetall_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hset"
            ) as hset_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.SequentialMessagesProcessor.check_if_user_input_exists"
            ) as check_if_user_input_exists_mock:
                check_if_user_input_exists_mock.return_value = True
                hgetall_mock.return_value = {
                    "case_id".encode(): None,
                    "hero_last_name".encode(): None,
                    "hero_first_name".encode(): None,
                    "hero_patronymic".encode(): None,
                    "hero_date_of_birth".encode(): None,
                    "item_used_for_dna_extraction".encode(): None,
                }
                process_sequential_message()
                hgetall_mock.assert_called_once()
                hset_mock.assert_called_once_with(
                    str(chat_id), mapping={"relative_last_name": message_text}
                )

        with self.subTest():
            with mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hgetall",
            ) as hgetall_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hset"
            ) as hset_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.SequentialMessagesProcessor.check_if_user_input_exists"
            ) as check_if_user_input_exists_mock:
                check_if_user_input_exists_mock.return_value = True
                hgetall_mock.return_value = {
                    "case_id".encode(): None,
                    "hero_last_name".encode(): None,
                    "hero_first_name".encode(): None,
                    "hero_patronymic".encode(): None,
                    "hero_date_of_birth".encode(): None,
                    "item_used_for_dna_extraction".encode(): None,
                    "relative_last_name".encode(): None,
                }
                process_sequential_message()
                hgetall_mock.assert_called_once()
                hset_mock.assert_called_once_with(
                    str(chat_id), mapping={"relative_first_name": message_text}
                )

        with self.subTest():
            with mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hgetall",
            ) as hgetall_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hset"
            ) as hset_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.SequentialMessagesProcessor.check_if_user_input_exists"
            ) as check_if_user_input_exists_mock:
                check_if_user_input_exists_mock.return_value = True
                hgetall_mock.return_value = {
                    "case_id".encode(): None,
                    "hero_last_name".encode(): None,
                    "hero_first_name".encode(): None,
                    "hero_patronymic".encode(): None,
                    "hero_date_of_birth".encode(): None,
                    "item_used_for_dna_extraction".encode(): None,
                    "relative_last_name".encode(): None,
                    "relative_first_name".encode(): None,
                }
                process_sequential_message()
                hgetall_mock.assert_called_once()
                hset_mock.assert_called_once_with(
                    str(chat_id), mapping={"relative_patronymic": message_text}
                )

        with self.subTest():
            with mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hgetall",
            ) as hgetall_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hset"
            ) as hset_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.SequentialMessagesProcessor.check_if_user_input_exists"
            ) as check_if_user_input_exists_mock:
                check_if_user_input_exists_mock.return_value = True
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
                }
                process_sequential_message()
                hgetall_mock.assert_called_once()
                hset_mock.assert_called_once_with(
                    str(chat_id), mapping={"is_added_to_dna_db": message_text}
                )

        with self.subTest():
            with mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hgetall",
            ) as hgetall_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hset"
            ) as hset_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.SequentialMessagesProcessor.check_if_user_input_exists"
            ) as check_if_user_input_exists_mock:
                check_if_user_input_exists_mock.return_value = True
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
                }
                process_sequential_message()
                hgetall_mock.assert_called_once()
                hset_mock.assert_called_once_with(
                    str(chat_id), mapping={"comment": message_text}
                )

        with self.subTest():
            with mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hgetall",
            ) as hgetall_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hset"
            ) as hset_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.SequentialMessagesProcessor.check_if_user_input_exists"
            ) as check_if_user_input_exists_mock:
                check_if_user_input_exists_mock.return_value = True
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
                with self.assertRaises(AllDataReceivedException):
                    process_sequential_message()
                    hgetall_mock.assert_called_once()
                    hset_mock.assert_not_called()

    @mock.patch("telegram_bot.sequential_messages_processor.client")
    def test_validate_input(self, redis_mock):
        with self.subTest():
            redis_mock.hgetall.return_value = {}
            message_data = "some_message_data"
            chat_id = "123123"
            processor = SequentialMessagesProcessor(
                message_data=message_data,
                user_id=int(chat_id),
            )
            processor._validate_user_input(message_data)

        with self.subTest():
            with self.assertRaises(UserMessageValidationFailedException):
                redis_mock.hgetall.return_value = {
                    b"case_id": "123123",
                    b"hero_last_name": "AAA",
                    b"hero_first_name": "BBB",
                    b"hero_patronymic": "CCC",
                }
                message_data = "1-1-2022"
                chat_id = "123123"
                processor = SequentialMessagesProcessor(
                    message_data=message_data,
                    user_id=int(chat_id),
                )
                processor._validate_user_input(message_data)
