from unittest import mock

from telegram_bot.exceptions import AllDataReceivedException
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

        def process_sequential_message():
            processor = SequentialMessagesProcessor(message_text, chat_id)
            processor.save_message()

        with self.subTest():
            with mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hgetall",
            ) as hgetall_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hset"
            ) as hset_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.expire"
            ) as expire_mock:
                hgetall_mock.return_value = {}
                process_sequential_message()
                hgetall_mock.assert_called_once()
                hset_mock.assert_called_once_with(
                    str(chat_id), mapping={"case_id": message_text}
                )
                expire_mock.assert_called_once_with(str(chat_id), 60 * 30)

        with self.subTest():
            with mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hgetall",
            ) as hgetall_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.hset"
            ) as hset_mock, mock.patch(
                "telegram_bot.sequential_messages_processor.redis.Redis.expire"
            ) as expire_mock:
                hgetall_mock.return_value = {"case_id".encode(): None}
                process_sequential_message()
                hgetall_mock.assert_called_once()
                hset_mock.assert_called_once_with(
                    str(chat_id), mapping={"hero_last_name": message_text}
                )
                expire_mock.assert_not_called()

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
                process_sequential_message()
                hgetall_mock.assert_called_once()
                hset_mock.assert_called_once_with(
                    str(chat_id), mapping={"hero_first_name": message_text}
                )
                expire_mock.assert_not_called()

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
                }
                process_sequential_message()
                hgetall_mock.assert_called_once()
                hset_mock.assert_called_once_with(
                    str(chat_id), mapping={"hero_patronymic": message_text}
                )
                expire_mock.assert_not_called()

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
                }
                process_sequential_message()
                hgetall_mock.assert_called_once()
                hset_mock.assert_called_once_with(
                    str(chat_id), mapping={"hero_date_of_birth": message_text}
                )
                expire_mock.assert_not_called()

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
                }
                process_sequential_message()
                hgetall_mock.assert_called_once()
                hset_mock.assert_called_once_with(
                    str(chat_id), mapping={"item_used_for_dna_extraction": message_text}
                )
                expire_mock.assert_not_called()

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
                }
                process_sequential_message()
                hgetall_mock.assert_called_once()
                hset_mock.assert_called_once_with(
                    str(chat_id), mapping={"relative_last_name": message_text}
                )
                expire_mock.assert_not_called()

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
                }
                process_sequential_message()
                hgetall_mock.assert_called_once()
                hset_mock.assert_called_once_with(
                    str(chat_id), mapping={"relative_first_name": message_text}
                )
                expire_mock.assert_not_called()

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
                }
                process_sequential_message()
                hgetall_mock.assert_called_once()
                hset_mock.assert_called_once_with(
                    str(chat_id), mapping={"relative_patronymic": message_text}
                )
                expire_mock.assert_not_called()

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
                }
                process_sequential_message()
                hgetall_mock.assert_called_once()
                hset_mock.assert_called_once_with(
                    str(chat_id), mapping={"is_added_to_dna_db": message_text}
                )
                expire_mock.assert_not_called()

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
                }
                process_sequential_message()
                hgetall_mock.assert_called_once()
                hset_mock.assert_called_once_with(
                    str(chat_id), mapping={"comment": message_text}
                )
                expire_mock.assert_not_called()

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
                with self.assertRaises(AllDataReceivedException):
                    process_sequential_message()
                    hgetall_mock.assert_called_once()
                    hset_mock.assert_not_called()
                    expire_mock.assert_not_called()
