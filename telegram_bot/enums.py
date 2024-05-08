from enum import IntEnum


class UserActionType(IntEnum):
    ADD_BOT_TO_CHAT = 1
    REMOVE_BOT_FROM_CHAT = 2
    OTHER = 99

    @classmethod
    def from_payload_value(cls, payload_value: str):
        if payload_value.lower() == "member":
            return cls.ADD_BOT_TO_CHAT
        elif payload_value.lower() in ("left", "kicked"):
            return cls.REMOVE_BOT_FROM_CHAT
        raise NotImplementedError


class ChatType(IntEnum):
    PRIVATE = 1
    GROUP = 2

    @classmethod
    def from_payload_value(cls, payload_value: str):
        if payload_value.lower() == "private":
            return cls.PRIVATE
        elif payload_value.lower() == "group":
            return cls.GROUP
        raise NotImplementedError


class MessageType(IntEnum):
    COMMAND = 1
    OTHER = 99

    @classmethod
    def from_payload_value(cls, payload_value: str):
        if payload_value.lower() == "bot_command":
            return cls.COMMAND
        raise NotImplementedError
