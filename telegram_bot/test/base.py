import json

from django.test import TestCase
from rest_framework.test import APITestCase

from telegram_bot.test.requests_examples import (
    BOT_KICKED_FROM_THE_PRIVATE_CHAT,
    BOT_ADDED_TO_THE_PRIVATE_CHAT,
    COMMAND_AS_MESSAGE_IN_PRIVATE_CHAT,
    COMMAND_AS_CALLBACK_IN_PRIVATE_CHAT,
    MESSAGE_IN_PRIVATE_CHAT,
    BOT_ADDED_TO_THE_GROUP,
    BOT_KICKED_FROM_THE_GROUP_1,
    COMMAND_AS_MESSAGE_IN_GROUP_CHAT,
)


class TelegramBotRequestsTestBase(APITestCase):
    def setUp(self):
        # Private chat
        self.bot_kicked_from_private_chat_request_payload = json.dumps(
            BOT_KICKED_FROM_THE_PRIVATE_CHAT
        )
        self.bot_added_to_the_private_chat_request_payload = (
            BOT_ADDED_TO_THE_PRIVATE_CHAT
        )
        self.command_as_message_in_private_chat_request_payload = (
            COMMAND_AS_MESSAGE_IN_PRIVATE_CHAT
        )
        self.command_as_callback_in_private_chat_request_payload = (
            COMMAND_AS_CALLBACK_IN_PRIVATE_CHAT
        )
        self.message_in_private_chat_request_payload = MESSAGE_IN_PRIVATE_CHAT

        # Group
        self.bot_added_to_the_group_request_payload = BOT_ADDED_TO_THE_GROUP
        self.bot_kicked_from_the_group_request_payload = BOT_KICKED_FROM_THE_GROUP_1
        self.command_as_message_in_group_request_payload = (
            COMMAND_AS_MESSAGE_IN_GROUP_CHAT
        )

        # TODO: add command as callback, message, bot set as admin, all for groups.
