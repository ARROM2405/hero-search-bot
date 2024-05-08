from abc import abstractmethod, ABC

from telegram_bot.dataclasses import StatusChangeWithinChat, UserMessage, BotCommand
from telegram_bot.enums import ChatType


class BaseParser(ABC):

    @staticmethod
    @abstractmethod
    def parse(telegram_message: dict) -> UserMessage | StatusChangeWithinChat: ...


class UserMessageParser(BaseParser):

    @staticmethod
    def parse(telegram_message: dict) -> UserMessage:
        entities = telegram_message["message"].get("entities")
        chat = telegram_message["message"].get("chat")
        return UserMessage(
            chat_id=telegram_message["message"]["from"]["id"],
            username=telegram_message["message"]["from"].get("username"),
            text=telegram_message["message"]["text"],
            first_name=telegram_message["message"]["from"].get("first_name"),
            last_name=telegram_message["message"]["from"].get("last_name"),
            message_type=entities[0]["type"] if entities else None,
            chat_type=(
                ChatType.from_payload_value(telegram_message["message"]["chat"]["type"])
                if chat and entities
                else None
            ),
        )


class ChatStatusChangeMessageParser(BaseParser):

    @staticmethod
    def parse(telegram_message: dict) -> StatusChangeWithinChat:
        telegram_message = telegram_message["my_chat_member"]
        chat_data = telegram_message["chat"]
        chat_member_data = telegram_message["new_chat_member"]
        author_data = telegram_message["from"]

        return StatusChangeWithinChat(
            chat_id=chat_data["id"],
            chat_type=ChatType.from_payload_value(chat_data["type"]),
            status=chat_member_data["status"],
            username=author_data.get("username"),
            first_name=author_data.get("first_name"),
            last_name=author_data.get("last_name"),
        )


class TelegramCommandParser(BaseParser):

    @staticmethod
    def _parse_command_as_callback_query(callback_query: dict) -> BotCommand:
        data = callback_query["data"]
        replied_message = callback_query["message"]
        replied_message_id = replied_message["message_id"]
        chat_data = replied_message["chat"]
        author_data = replied_message["from"]

        return BotCommand(
            chat_id=chat_data["id"],
            chat_type=ChatType.from_payload_value(chat_data["type"]),
            username=author_data.get("username"),
            data=data,
            replied_message_id=replied_message_id,
            first_name=author_data.get("first_name"),
            last_name=author_data.get("last_name"),
        )

    @staticmethod
    def _parse_command_as_message(message: dict) -> BotCommand:
        data = message["text"]
        author_data = message["from"]
        chat_data = message["chat"]
        replied_message_id = None

        return BotCommand(
            chat_id=chat_data["id"],
            chat_type=ChatType.from_payload_value(chat_data["type"]),
            username=author_data.get("username"),
            data=data,
            replied_message_id=replied_message_id,
            first_name=author_data.get("first_name"),
            last_name=author_data.get("last_name"),
        )

    @staticmethod
    def parse(telegram_message: dict) -> BotCommand:
        if callback_query := telegram_message.get("callback_query"):
            return TelegramCommandParser._parse_command_as_callback_query(
                callback_query
            )

        elif message := telegram_message.get("message"):
            return TelegramCommandParser._parse_command_as_message(message)
