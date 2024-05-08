from telegram_bot.message_handling_services import (
    MessageHandler,
    MemberStatusChangeProcessor,
)
from telegram_bot.serializers import TelegramBotSerializer
from telegram_bot.test.base import TelegramBotRequestsTestBase


class TestMessageHandler(TelegramBotRequestsTestBase):
    def setUp(self):
        super().setUp()

    def _get_serialized_request_data(self, request_payload: dict) -> dict:
        serializer = TelegramBotSerializer(data=request_payload)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data

    def test_get_message_processor_for_bot_added_to_group_action(self):
        serialized_data = self._get_serialized_request_data(
            self.bot_added_to_the_group_request_payload
        )
        message_handler = MessageHandler(telegram_message=serialized_data)
        processor = message_handler._get_message_processor()
        assert isinstance(processor, MemberStatusChangeProcessor)

    def test_get_message_processor_for_bot_kicked_to_group_action(self):
        serialized_data = self._get_serialized_request_data(
            self.bot_kicked_from_the_group_request_payload
        )
        message_handler = MessageHandler(telegram_message=serialized_data)
        processor = message_handler._get_message_processor()
        assert isinstance(processor, MemberStatusChangeProcessor)

    def test_get_message_processor_for_command_as_message_in_private_chat(self):
        raise AssertionError

    def test_get_message_processor_for_command_as_callback_in_private_chat(self):
        raise AssertionError

    def test_get_message_processor_for_message_in_private_chat(self):
        raise AssertionError
