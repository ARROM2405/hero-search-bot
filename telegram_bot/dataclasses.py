import json
from dataclasses import dataclass, asdict

from telegram_bot.enums import ChatType, MessageType


@dataclass
class UserMessage:
    chat_id: int
    username: str
    text: str
    chat_type: ChatType = None
    message_type: MessageType = None
    first_name: str = None
    last_name: str = None


@dataclass
class StatusChangeWithinChat:
    chat_id: int
    chat_type: ChatType
    status: str
    username: str
    user_id: int
    first_name: str = None
    last_name: str = None


@dataclass
class BotCommand:
    chat_id: int
    chat_type: ChatType
    username: str | None
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

    def to_payload(self) -> dict:
        payload = asdict(self)
        if self.reply_markup:
            payload["reply_markup"] = json.dumps(self.reply_markup)
        return payload


@dataclass
class ChatData:
    id: int
    type: ChatType
