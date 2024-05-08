from unittest import mock

from django.test import TestCase

from telegram_bot.sequential_messages_processor import SequentialMessagesProcessor


class TestSequentialMessagesProcessor(TestCase):
    def setUp(self):
        pass

    @mock.patch("telegram_bot.sequential_messages_processor.client")
    def test_get_current_and_next_message_keys(self, redis_mock):
        message_data = "some_message_data"
        chat_id = "123123"
        with self.subTest():
            redis_mock.hgetall.return_value = {}
            processor = SequentialMessagesProcessor(
                message_data=message_data,
                chat_id=chat_id,
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
                chat_id=chat_id,
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
                chat_id=chat_id,
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
                chat_id=chat_id,
            )
            assert (
                processor.current_message_key,
                processor.next_message_key,
            ) == (
                "comment",
                None,
            )
