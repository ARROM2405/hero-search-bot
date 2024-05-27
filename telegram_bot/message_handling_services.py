from abc import ABC, abstractmethod

import requests

from telegram_bot.constants import BASE_URL, MESSAGES_MAPPING
from telegram_bot.dataclasses import ResponseMessage
from telegram_bot.enums import UserActionType, ChatType
from telegram_bot.exceptions import (
    TelegramMessageNotParsedException,
    AllDataReceivedException,
)
from telegram_bot.messages_texts import (
    FIRST_INSTRUCTIONS,
    INPUT_NOT_CONFIRMED_RESPONSE,
    INPUT_CONFIRMED_RESPONSE,
    ALL_DATA_RECEIVED_RESPONSE,
)
from telegram_bot.models import DataEntryAuthor
from telegram_bot.parsers import (
    ChatStatusChangeMessageParser,
    UserMessageParser,
    TelegramCommandParser,
)
from telegram_bot.sequential_messages_processor import SequentialMessagesProcessor


class TelegramMessageProcessorBase(ABC):
    PARSER = None

    def __init__(self, telegram_message: dict):
        self.telegram_message = telegram_message
        self.parsed_telegram_message = None

    @abstractmethod
    def process(self): ...

    @abstractmethod
    def prepare_response(self) -> ResponseMessage: ...


# TODO: check if needed?
class MemberStatusChangeProcessor(TelegramMessageProcessorBase):
    PARSER = ChatStatusChangeMessageParser

    def process(self):
        self.parsed_telegram_message = self.PARSER.parse(self.telegram_message)

    def prepare_response(self) -> dict:
        action_type = UserActionType.from_payload_value(
            self.parsed_telegram_message.status
        )
        if (
            self.parsed_telegram_message.chat_type is ChatType.PRIVATE
            and action_type is UserActionType.ADD_BOT_TO_CHAT
        ):
            response_text = FIRST_INSTRUCTIONS
            response_reply_markup = {
                "remove_keyboard": True,
                "inline_keyboard": [
                    [
                        {
                            "text": "Зрозуміло, починаємо",
                            "callback_data": "/instructions_confirmed",
                        }
                    ]
                ],
            }
            response_object = ResponseMessage(
                text=response_text,
                reply_markup=response_reply_markup,
                chat_id=self.parsed_telegram_message.chat_id,
            )
            payload = response_object.to_payload()
            return payload


class UserMessageProcessor(TelegramMessageProcessorBase):
    PARSER = UserMessageParser

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sequential_messages_processor = None
        self.all_data_received = False

    def _prepare_sequential_messages_processor(self):
        if not self.parsed_telegram_message:
            raise TelegramMessageNotParsedException
        self.sequential_messages_processor = SequentialMessagesProcessor(
            message_data=self.parsed_telegram_message.text,
            chat_id=self.parsed_telegram_message.chat_id,
        )

    def process(self):
        self.parsed_telegram_message = self.PARSER.parse(self.telegram_message)
        print("parsed_message", self.parsed_telegram_message)
        try:
            self._prepare_sequential_messages_processor()
            self.sequential_messages_processor.save_message()
        except AllDataReceivedException:
            self.all_data_received = True

    def prepare_response(self) -> dict:
        reply_markup = None
        if not self.sequential_messages_processor and self.all_data_received:
            response_text = ALL_DATA_RECEIVED_RESPONSE
        else:
            try:
                response_text = self.sequential_messages_processor.get_response_text()

            except AllDataReceivedException:
                response_text = (
                    self.sequential_messages_processor.get_completed_input_confirmation_text()
                )
                reply_markup = {
                    "inline_keyboard": [
                        [
                            {
                                "text": "Дані корректні.",
                                "callback_data": "/input_confirmed",
                            }
                        ],
                        [
                            {
                                "text": "Дані не корректні. Маю відредагувати.",
                                "callback_data": "/input_not_confirmed",
                            }
                        ],
                    ],
                }
        response_object = ResponseMessage(
            text=response_text,
            chat_id=self.parsed_telegram_message.chat_id,
        )
        if reply_markup:
            response_object.reply_markup = reply_markup
        print("response_object", response_object)
        payload = response_object.to_payload()
        return payload


class BotCommandProcessor(TelegramMessageProcessorBase):
    PARSER = TelegramCommandParser

    def _remove_inline_keyboard_from_replied_message(
        self, chat_id: int, message_id: int
    ):
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "reply_markup": {"inline_keyboard": []},
        }
        _response = requests.post(url=BASE_URL + "editMessageReplyMarkup", json=payload)

    def process(self):
        self.parsed_telegram_message = self.PARSER.parse(self.telegram_message)
        print("parsed_message", self.parsed_telegram_message)
        if self.parsed_telegram_message.sent_by_inline_keyboard:
            self._remove_inline_keyboard_from_replied_message(
                chat_id=self.parsed_telegram_message.chat_id,
                message_id=self.parsed_telegram_message.replied_message_id,
            )
        match self.parsed_telegram_message.data:
            case "/start":
                self._process_start_command()
            case "/instructions_confirmed":
                self._process_instructions_confirmed_command()
            case "/input_confirmed":
                self._process_input_confirmed_command()
            case "/input_not_confirmed":
                self._process_input_not_confirmed_command()

    def _process_start_command(self):
        pass

    def _process_instructions_confirmed_command(self):
        pass

    def _process_input_confirmed_command(self):
        data_entry_author, _ = DataEntryAuthor.objects.get_or_create(
            telegram_id=self.parsed_telegram_message.chat_id,
            defaults={
                "telegram_id": self.parsed_telegram_message.chat_id,
                "username": self.parsed_telegram_message.username,
                "first_name": self.parsed_telegram_message.first_name,
                "last_name": self.parsed_telegram_message.last_name,
            },
        )
        SequentialMessagesProcessor.save_confirmed_data(
            chat_id=self.parsed_telegram_message.chat_id,
            entry_author=data_entry_author,
        )

    def _process_input_not_confirmed_command(self):
        SequentialMessagesProcessor.remove_incorrect_input(
            self.parsed_telegram_message.chat_id
        )

    def _get_start_command_response(self) -> dict:
        response_text = FIRST_INSTRUCTIONS
        response_reply_markup = {
            "inline_keyboard": [
                [
                    {
                        "text": "Зрозуміло, починаємо",
                        "callback_data": "/instructions_confirmed",
                    }
                ]
            ],
        }

        response_object = ResponseMessage(
            text=response_text,
            reply_markup=response_reply_markup,
            chat_id=self.parsed_telegram_message.chat_id,
        )
        print("response_object", response_object)
        payload = response_object.to_payload()
        return payload

    def _get_instructions_confirmed_command_response(self) -> dict:
        response_text = MESSAGES_MAPPING["case_id"]
        response_object = ResponseMessage(
            text=response_text,
            chat_id=self.parsed_telegram_message.chat_id,
        )
        print("response_object", response_object)
        payload = response_object.to_payload()
        return payload

    def _get_input_confirmed_command_response(self) -> dict:
        response_object = ResponseMessage(
            text=INPUT_CONFIRMED_RESPONSE,
            chat_id=self.parsed_telegram_message.chat_id,
        )
        print("response_object", response_object)
        payload = response_object.to_payload()
        return payload

    def _get_input_not_confirmed_command_response(self) -> dict:
        response_text = INPUT_NOT_CONFIRMED_RESPONSE
        response_reply_markup = {
            "inline_keyboard": [
                [
                    {
                        "text": "Зрозуміло, починаємо",
                        "callback_data": "/instructions_confirmed",
                    }
                ]
            ],
        }

        response_object = ResponseMessage(
            text=response_text,
            reply_markup=response_reply_markup,
            chat_id=self.parsed_telegram_message.chat_id,
        )
        print("response_object", response_object)
        payload = response_object.to_payload()
        return payload

    def prepare_response(self) -> dict | None:
        if self.parsed_telegram_message.chat_type is not ChatType.GROUP:
            match self.parsed_telegram_message.data:
                case "/start":
                    return self._get_start_command_response()
                case "/instructions_confirmed":
                    return self._get_instructions_confirmed_command_response()
                case "/input_confirmed":
                    return self._get_input_confirmed_command_response()
                case "/input_not_confirmed":
                    return self._get_input_not_confirmed_command_response()


class MessageHandler:
    def __init__(self, telegram_message: dict):
        self.telegram_message = telegram_message

    def _get_message_processor(self):
        if "callback_query" in self.telegram_message:
            return BotCommandProcessor(self.telegram_message)
        elif "message" in self.telegram_message:
            if entities := self.telegram_message["message"].get("entities"):
                if entities[0]["type"] == "bot_command":
                    return BotCommandProcessor(self.telegram_message)
            elif "left_chat_member" in self.telegram_message["message"]:
                return MemberStatusChangeProcessor(self.telegram_message)
            return UserMessageProcessor(self.telegram_message)
        elif "my_chat_member" in self.telegram_message:
            return MemberStatusChangeProcessor(self.telegram_message)
        raise NotImplementedError

    @staticmethod
    def _get_response_url() -> str:
        return BASE_URL + "sendMessage"

    def _send_response(self, response: dict):
        url = self._get_response_url()
        print(url)
        print(response)
        response_call = requests.post(url=url, data=response)
        print(response_call.status_code, response_call.text)

    def handle_telegram_message(self):
        processor = self._get_message_processor()
        processor.process()
        response = processor.prepare_response()
        if response:
            self._send_response(response)
