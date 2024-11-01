import datetime
import os
from abc import ABC, abstractmethod

import requests
from django.conf import settings

from telegram_bot.constants import (
    BASE_URL,
    MESSAGES_MAPPING,
    DATE_FORMAT,
    MESSAGE_TEXT_VALIDATION_FAILED,
    MESSAGE_USER_INPUT_EXPIRED,
)
from telegram_bot.dataclasses import ResponseMessage
from telegram_bot.enums import ChatType
from telegram_bot.exceptions import (
    TelegramMessageNotParsedException,
    AllDataReceivedException,
    UnknownCommandException,
    UnauthorizedUserCalledReportGenerationException,
    UserInputExpiredException,
    UserMessageValidationFailedException,
)
from telegram_bot.messages_texts import (
    FIRST_INSTRUCTIONS,
    INPUT_NOT_CONFIRMED_RESPONSE,
    INPUT_CONFIRMED_RESPONSE,
    ALL_DATA_RECEIVED_RESPONSE,
    EDITED_MESSAGE_RESPONSE,
)
from telegram_bot.models import TelegramUser, BotStatusChange
from telegram_bot.parsers import (
    ChatStatusChangeMessageParser,
    UserMessageParser,
    TelegramCommandParser,
)
from telegram_bot.report_generator import ReportGenerator
from telegram_bot.sequential_messages_processor import SequentialMessagesProcessor
from telegram_bot.types import ResponsePayload

from telegram_bot.logger_config import logger


class UserInputExpiredResponseMixin:
    def _get_user_input_expired_response(self):
        response_object = ResponseMessage(
            text=MESSAGE_USER_INPUT_EXPIRED,
            chat_id=self.parsed_telegram_message.chat_id,
        )
        payload = response_object.to_payload()
        return payload


class TelegramMessageProcessorBase(ABC):
    PARSER = None

    def __init__(self, telegram_message: dict):
        self.telegram_message = telegram_message
        self.parsed_telegram_message = None

    @abstractmethod
    def process(self): ...

    @abstractmethod
    def prepare_response(self) -> dict | None: ...

    @abstractmethod
    def finalize(self): ...


class MemberStatusChangeProcessor(TelegramMessageProcessorBase):
    PARSER = ChatStatusChangeMessageParser

    def _save_bot_status_change(self) -> BotStatusChange:
        telegram_user, created = TelegramUser.objects.get_or_create(
            telegram_id=self.parsed_telegram_message.user_id,
            first_name=self.parsed_telegram_message.first_name,
            last_name=self.parsed_telegram_message.last_name,
            username=self.parsed_telegram_message.username,
        )

        if created:
            logger.info(
                f"Created user: username: telegram_id: {telegram_user}, {self.parsed_telegram_message.username}, first_name: {self.parsed_telegram_message}, last_name: {self.parsed_telegram_message}"
            )

        return BotStatusChange.objects.create(
            initiator=telegram_user,
            chat_id=self.parsed_telegram_message.chat_id,
            action_type=self.parsed_telegram_message.user_action_type,
            chat_type=self.parsed_telegram_message.chat_type,
        )

    def process(self):
        logger.info(
            f"Processing bot status change message: {self.parsed_telegram_message}"
        )
        self.parsed_telegram_message = self.PARSER.parse(self.telegram_message)
        self._save_bot_status_change()

    def prepare_response(self):
        pass

    def finalize(self):
        pass


class UserMessageProcessor(TelegramMessageProcessorBase, UserInputExpiredResponseMixin):
    PARSER = UserMessageParser

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sequential_messages_processor = None
        self.all_data_received = False
        self.message_validation_passed = None
        self.user_input_expired = False

    def _prepare_sequential_messages_processor(self):
        if not self.parsed_telegram_message:
            raise TelegramMessageNotParsedException
        self.sequential_messages_processor = SequentialMessagesProcessor(
            message_data=self.parsed_telegram_message.text,
            user_id=self.parsed_telegram_message.chat_id,
        )

    def process(self):
        self.parsed_telegram_message = self.PARSER.parse(self.telegram_message)
        logger.info(f"Processing user message: {self.parsed_telegram_message}")
        try:
            self._prepare_sequential_messages_processor()
            if not self.parsed_telegram_message.message_edition:
                self.sequential_messages_processor.save_message()
        except AllDataReceivedException:
            self.all_data_received = True
        except UserMessageValidationFailedException as e:
            logger.exception(f"Exception: {e}")
            self.message_validation_passed = False
        except UserInputExpiredException as e:
            logger.exception(f"Exception: {e}")
            self.user_input_expired = True

    def prepare_response(self) -> ResponsePayload | None:
        if self.user_input_expired:
            return self._get_user_input_expired_response()
        if self.message_validation_passed is False:
            return self._get_message_validation_failed_response()
        if "edited_message" in self.telegram_message:
            return self._get_message_edition_response()
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
        payload = response_object.to_payload()
        return payload

    def _get_message_edition_response(self) -> ResponsePayload:
        if self.sequential_messages_processor.check_if_user_input_exists(
            self.parsed_telegram_message.user_id
        ):
            response_object = ResponseMessage(
                text=EDITED_MESSAGE_RESPONSE,
                chat_id=self.parsed_telegram_message.chat_id,
                reply_markup={
                    "inline_keyboard": [
                        [
                            {
                                "text": "Почати вводити дані з початку.",
                                "callback_data": "/remove_and_restart_input",
                            }
                        ],
                        [
                            {
                                "text": "Продовжую як є.",
                                "callback_data": "/continue_input",
                            }
                        ],
                    ],
                },
            )
            payload = response_object.to_payload()
            return payload

    def _get_message_validation_failed_response(self):
        response_object = ResponseMessage(
            text=f"{MESSAGE_TEXT_VALIDATION_FAILED}\n{MESSAGES_MAPPING[self.sequential_messages_processor.current_message_key]}",
            chat_id=self.parsed_telegram_message.chat_id,
            reply_markup={
                "inline_keyboard": [
                    {
                        "text": "Почати вводити дані з початку.",
                        "callback_data": "/start",
                    }
                ],
            },
        )
        payload = response_object.to_payload()
        return payload

    def finalize(self):
        pass


class BotCommandProcessor(TelegramMessageProcessorBase, UserInputExpiredResponseMixin):
    PARSER = TelegramCommandParser

    def __init__(self, telegram_message: dict):
        super().__init__(telegram_message)
        self.user_input_expired = False

    def _remove_inline_keyboard_from_replied_message(
        self, chat_id: int, message_id: int
    ):
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "reply_markup": {"inline_keyboard": []},
        }
        _response = requests.post(url=BASE_URL + "editMessageReplyMarkup", json=payload)

    def _dispatch_processing(self):
        match self.parsed_telegram_message.data:
            case "/start":
                self._process_start_command()
            case "/instructions_confirmed":
                self._process_instructions_confirmed_command()
            case "/input_confirmed":
                self._process_input_confirmed_command()
            case "/input_not_confirmed":
                self._process_input_not_confirmed_command()
            case "/remove_and_restart_input":
                self._process_remove_and_restart_input_command()
            case "/continue_input":
                self._process_continue_input_command()
            case command if command.startswith("/report_"):
                self._process_report_generation_command()
            case _:
                raise UnknownCommandException

    def process(self):
        self.parsed_telegram_message = self.PARSER.parse(self.telegram_message)
        logger.info(f"Processing bot command: {self.parsed_telegram_message}")
        if self.parsed_telegram_message.sent_by_inline_keyboard:
            self._remove_inline_keyboard_from_replied_message(
                chat_id=self.parsed_telegram_message.chat_id,
                message_id=self.parsed_telegram_message.replied_message_id,
            )
        try:
            self._dispatch_processing()
        except UserInputExpiredException as e:
            logger.error(f"Exception occurred {e}")
            self.user_input_expired = True

    def _process_start_command(self):
        pass

    def _process_instructions_confirmed_command(self):
        SequentialMessagesProcessor.create_new_redis_entry(
            user_id=self.parsed_telegram_message.chat_id
        )

    def _process_input_confirmed_command(self):
        data_entry_author, _ = TelegramUser.objects.get_or_create(
            telegram_id=self.parsed_telegram_message.user_id,
            defaults={
                "telegram_id": self.parsed_telegram_message.user_id,
                "username": self.parsed_telegram_message.username,
                "first_name": self.parsed_telegram_message.first_name,
                "last_name": self.parsed_telegram_message.last_name,
            },
        )
        SequentialMessagesProcessor.save_confirmed_data(
            user_id=self.parsed_telegram_message.user_id,
            entry_author=data_entry_author,
        )

    def _process_input_not_confirmed_command(self):
        SequentialMessagesProcessor.remove_incorrect_input(
            self.parsed_telegram_message.user_id
        )

    def _process_remove_and_restart_input_command(self):
        SequentialMessagesProcessor.remove_incorrect_input(
            self.parsed_telegram_message.user_id
        )

    def _process_continue_input_command(self):
        pass

    def _process_report_generation_command(self):
        if settings.ADMIN_USER_IDS:
            if self.parsed_telegram_message.chat_id not in settings.ADMIN_USER_IDS:
                raise UnauthorizedUserCalledReportGenerationException
        report_dates = self.parsed_telegram_message.data.split("_")[1:]
        self.generated_report = ReportGenerator(
            start_date=datetime.datetime.strptime(report_dates[0], DATE_FORMAT),
            end_date=datetime.datetime.strptime(report_dates[1], DATE_FORMAT),
        ).generate_report()

    def _get_start_command_response(self) -> ResponsePayload:
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
        payload = response_object.to_payload()
        return payload

    def _get_instructions_confirmed_command_response(self) -> ResponsePayload:
        response_text = MESSAGES_MAPPING["case_id"]
        response_object = ResponseMessage(
            text=response_text,
            chat_id=self.parsed_telegram_message.chat_id,
        )
        payload = response_object.to_payload()
        return payload

    def _get_input_confirmed_command_response(self) -> ResponsePayload:
        response_object = ResponseMessage(
            text=INPUT_CONFIRMED_RESPONSE,
            chat_id=self.parsed_telegram_message.chat_id,
        )
        payload = response_object.to_payload()
        return payload

    def _get_input_not_confirmed_command_response(self) -> ResponsePayload:
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
        payload = response_object.to_payload()
        return payload

    def _get_remove_and_restart_input_command_response(self):
        return self._get_instructions_confirmed_command_response()

    def _get_continue_input_command_response(self) -> ResponsePayload:
        response_text = SequentialMessagesProcessor(
            message_data=None,
            user_id=self.parsed_telegram_message.user_id,
        ).get_response_text()
        response_object = ResponseMessage(
            text=response_text,
            chat_id=self.parsed_telegram_message.chat_id,
        )
        return response_object.to_payload()

    def _get_report_generation_command_response(self) -> ResponsePayload:
        return ResponseMessage(
            chat_id=self.parsed_telegram_message.chat_id,
            text="",
            file_path=self.generated_report,
        ).to_payload()

    def prepare_response(self) -> ResponsePayload | None:
        if self.parsed_telegram_message.chat_type is not ChatType.GROUP:
            if self.user_input_expired:
                return self._get_user_input_expired_response()
            match self.parsed_telegram_message.data:
                case "/start":
                    return self._get_start_command_response()
                case "/instructions_confirmed":
                    return self._get_instructions_confirmed_command_response()
                case "/input_confirmed":
                    return self._get_input_confirmed_command_response()
                case "/input_not_confirmed":
                    return self._get_input_not_confirmed_command_response()
                case "/remove_and_restart_input":
                    return self._get_remove_and_restart_input_command_response()
                case "/continue_input":
                    return self._get_continue_input_command_response()
                case command if command.startswith("/report_"):
                    return self._get_report_generation_command_response()
                case _:
                    raise UnknownCommandException

    def finalize(self):
        if hasattr(self, "generated_report"):
            os.remove(self.generated_report)


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
        elif "edited_message" in self.telegram_message:
            return UserMessageProcessor(self.telegram_message)

        elif "my_chat_member" in self.telegram_message:
            return MemberStatusChangeProcessor(self.telegram_message)
        raise NotImplementedError

    @staticmethod
    def _get_response_url(response: dict) -> str:
        if "files" in response:
            return BASE_URL + "sendDocument"
        return BASE_URL + "sendMessage"

    def _send_response(self, response: dict):
        logger.info(f"Prepared response: {response}")
        url = self._get_response_url(response)
        response_call = requests.post(url=url, **response)
        logger.info(
            f"Telegram response status for response sent: {response_call.status_code}, url: {url}"
        )

    def handle_telegram_message(self):
        processor = self._get_message_processor()
        logger.info(
            f"{processor.__class__.__name__} picked for {self.telegram_message} processing"
        )
        try:
            processor.process()
            response = processor.prepare_response()
            if response:
                self._send_response(response)
        except Exception as e:
            logger.exception(f"Exception: {e}")
            pass
        finally:
            processor.finalize()
