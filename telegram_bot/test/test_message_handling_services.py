from unittest import mock

from telegram_bot.message_handling_services import (
    MessageHandler,
    MemberStatusChangeProcessor,
    BotCommandProcessor,
    UserMessageProcessor,
)
from telegram_bot.messages_texts import FIRST_INSTRUCTIONS
from telegram_bot.serializers import TelegramBotSerializer
from telegram_bot.test.base import TelegramBotRequestsTestBase


class TestMessageHandler(TelegramBotRequestsTestBase):
    def setUp(self):
        super().setUp()

    def _get_serialized_request_data(self, request_payload: dict) -> dict:
        serializer = TelegramBotSerializer(data=request_payload)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data

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
