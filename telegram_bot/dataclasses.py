import json
from dataclasses import dataclass

from telegram_bot.enums import ChatType, MessageType, UserActionType
from telegram_bot.types import ResponsePayload


@dataclass
class UserMessage:
    chat_id: int | None
    username: str
    user_id: int
    text: str
    message_edition: bool
    chat_type: ChatType = None
    message_type: MessageType = None
    first_name: str = None
    last_name: str = None


@dataclass
class StatusChangeWithinChat:
    chat_id: int
    chat_type: ChatType
    user_action_type: UserActionType
    username: str
    user_id: int
    first_name: str = None
    last_name: str = None


@dataclass
class BotCommand:
    chat_id: int
    chat_type: ChatType
    username: str | None
    user_id: int
    data: str
    replied_message_id: int | None = None
    sent_by_inline_keyboard: bool = False
    first_name: str | None = None
    last_name: str | None = None


@dataclass
class ResponseMessage:
    text: str
    chat_id: int
    reply_markup: dict | None = None
    file_path: str = None

    def to_payload(self) -> ResponsePayload:
        payload: ResponsePayload = {
            "data": {"text": self.text, "chat_id": self.chat_id}
        }
        if self.reply_markup:
            payload["data"]["reply_markup"] = json.dumps(self.reply_markup)
        if self.file_path:
            payload["files"] = {"document": open(self.file_path, "rb")}
        return payload


@dataclass
class ChatData:
    id: int
    type: ChatType
