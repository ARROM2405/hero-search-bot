from abc import abstractmethod, ABC

from telegram_bot.dataclasses import (
    StatusChangeWithinChat,
    UserMessage,
    BotCommand,
)
from telegram_bot.enums import ChatType, MessageType, UserActionType


class BaseParser(ABC):

    @staticmethod
    @abstractmethod
    def parse(telegram_message: dict) -> UserMessage | StatusChangeWithinChat: ...


class UserMessageParser(BaseParser):

    @staticmethod
    def parse(telegram_message: dict) -> UserMessage:
        message = telegram_message["message"]
        chat = message.get("chat")
        return UserMessage(
            chat_id=chat.get("id") if chat else None,
            user_id=message["from"]["id"],
            username=message["from"].get("username"),
            text=message["text"],
            first_name=message["from"].get("first_name"),
            last_name=message["from"].get("last_name"),
            message_type=MessageType.from_message_object_in_payload(message),
            chat_type=(
                ChatType.from_payload_value(message["chat"]["type"]) if chat else None
            ),
        )


class ChatStatusChangeMessageParser(BaseParser):

    @staticmethod
    def _parse_user_action_type(telegram_message: dict) -> UserActionType:
        payload_value = (
            "left"
            if "left_chat_member" in telegram_message
            else telegram_message["new_chat_member"]["status"]
        )
        return UserActionType.from_payload_value(payload_value)

    @staticmethod
    def parse(telegram_message: dict) -> StatusChangeWithinChat:
        telegram_message = telegram_message.get(
            "my_chat_member"
        ) or telegram_message.get("message")
        chat_data = telegram_message["chat"]
        user_action_type = ChatStatusChangeMessageParser._parse_user_action_type(
            telegram_message
        )
        author_data = telegram_message["from"]

        return StatusChangeWithinChat(
            chat_id=chat_data["id"],
            chat_type=ChatType.from_payload_value(chat_data["type"]),
            user_action_type=user_action_type,
            username=author_data.get("username"),
            user_id=author_data["id"],
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
        author_data = callback_query["from"]
        sent_by_inline_keyboard = "inline_keyboard" in replied_message.get(
            "reply_markup", {}
        )

        return BotCommand(
            chat_id=chat_data["id"],
            chat_type=ChatType.from_payload_value(chat_data["type"]),
            username=author_data.get("username"),
            user_id=author_data["id"],
            data=data,
            replied_message_id=replied_message_id,
            sent_by_inline_keyboard=sent_by_inline_keyboard,
            first_name=author_data.get("first_name"),
            last_name=author_data.get("last_name"),
        )

    @staticmethod
    def _parse_command_as_message(message: dict) -> BotCommand:
        data = message["text"]
        author_data = message["from"]
        chat_data = message["chat"]

        return BotCommand(
            chat_id=chat_data["id"],
            chat_type=ChatType.from_payload_value(chat_data["type"]),
            username=author_data.get("username"),
            user_id=author_data["id"],
            data=data,
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
        raise NotImplementedError
