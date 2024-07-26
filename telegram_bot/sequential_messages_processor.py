import copy
import os
from datetime import datetime

import redis
from django.conf import settings
from dotenv import load_dotenv

from telegram_bot.constants import (
    ORDER_OF_MESSAGES,
    MESSAGES_MAPPING,
    MESSAGE_TEXT_VALIDATION_FAILED,
)
from telegram_bot.exceptions import AllDataReceivedException
from telegram_bot.models import HeroData, TelegramUser

load_dotenv(os.path.join(settings.BASE_DIR, ".env"))
client = redis.Redis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"), db=0)


class SequentialMessagesProcessor:
    def __init__(self, message_data: str | None, user_id: int):
        self.message_data = message_data
        self.user_id = user_id
        self.current_message_key, self.next_message_key = (
            self._get_current_and_next_message_keys()
        )
        self.message_validation_passed = self._validate_user_input(self.message_data)

    def _get_current_and_next_message_keys(self) -> tuple[str, str | None]:
        ordered_message_keys = copy.copy(ORDER_OF_MESSAGES)
        saved_messages = self.get_user_input(
            self.user_id
        )  # keys returned as a binary strings
        messages_not_provided_yet = [
            _ for _ in ordered_message_keys if _.encode() not in saved_messages
        ]
        if messages_not_provided_yet:
            current_message_key = messages_not_provided_yet[0]
            self.current_message_key = current_message_key
            if len(messages_not_provided_yet) == 1:
                next_message_key = None
            else:
                next_message_key = messages_not_provided_yet[1]
                self.next_message_key = next_message_key
            return current_message_key, next_message_key
        raise AllDataReceivedException  # TODO: Probably other type of error should be used here

    def _create_new_redis_saved_data_set(self, mapping: dict[str, str]):
        client.hset(str(self.user_id), mapping={**mapping})
        client.expire(str(self.user_id), 60 * 30)

    def save_message(self):
        if self.message_validation_passed:
            if self.current_message_key == ORDER_OF_MESSAGES[0]:
                self._create_new_redis_saved_data_set(
                    {self.current_message_key: self.message_data}
                )
            else:
                client.hset(
                    str(self.user_id),
                    mapping={self.current_message_key: self.message_data},
                )

    def get_response_text(self) -> str:
        if self.message_validation_passed is False:
            return f"{MESSAGE_TEXT_VALIDATION_FAILED}\n{MESSAGES_MAPPING[self.current_message_key]}"
        if self.next_message_key:
            return MESSAGES_MAPPING[self.next_message_key]
        raise AllDataReceivedException

    def get_completed_input_confirmation_text(self) -> str:
        input_data = self.get_user_input(user_id=self.user_id)
        return f"""Будьласка підтвердіть чи всі введені дані коректні.
        Номер справи в реєстрі: {input_data["case_id".encode()].decode()}
        Прізвище героя: {input_data["hero_last_name".encode()].decode()}
        Ім'я героя: {input_data["hero_first_name".encode()].decode()}
        Ім'я по батькові героя: {input_data["hero_patronymic".encode()].decode()}
        Дата народження героя: {input_data["hero_date_of_birth".encode()].decode()}
        Предмет використания для отримання зразка ДНК: {input_data["item_used_for_dna_extraction".encode()].decode()}
        Прізвище родича: {input_data["relative_last_name".encode()].decode()}
        Ім'я родича: {input_data["relative_first_name".encode()].decode()}
        Ім'я по батькові родича: {input_data["relative_patronymic".encode()].decode()}
        Дані є в реєстрі ДНК: {input_data["is_added_to_dna_db".encode()].decode()}
        Коментар: {input_data["comment".encode()].decode()}
        """

    @staticmethod
    def remove_incorrect_input(user_id: int):
        client.delete(str(user_id))

    @staticmethod
    def save_confirmed_data(user_id: int, entry_author: TelegramUser) -> HeroData:
        data = SequentialMessagesProcessor.get_user_input(user_id)
        print("saved_input:", end=" ")
        print(data)
        hero_data = HeroData.objects.create(
            case_id=int(data["case_id".encode()].decode()),
            hero_last_name=data["hero_last_name".encode()].decode(),
            hero_first_name=data["hero_first_name".encode()].decode(),
            hero_patronymic=data["hero_patronymic".encode()].decode(),
            hero_date_of_birth=datetime.strptime(
                data["hero_date_of_birth".encode()].decode(),
                "%d/%m/%Y",
            ).date(),
            item_used_for_dna_extraction=data[
                "item_used_for_dna_extraction".encode()
            ].decode(),
            relative_last_name=data["relative_last_name".encode()].decode(),
            relative_first_name=data["relative_first_name".encode()].decode(),
            relative_patronymic=data["relative_patronymic".encode()].decode(),
            is_added_to_dna_db=(
                True
                if data["is_added_to_dna_db".encode()].decode().lower() == "так"
                else False
            ),
            comment=(
                ""
                if data["comment".encode()].decode().lower() == "ні"
                else data["comment".encode()].decode()
            ),
            author=entry_author,
        )
        client.delete(user_id)
        return hero_data

    @staticmethod
    def get_user_input(user_id: int) -> dict:
        return client.hgetall(str(user_id))

    @staticmethod
    def check_if_user_input_exists(user_id: int) -> bool:
        if SequentialMessagesProcessor.get_user_input(user_id):
            return True
        return False

    def _validate_user_input(self, value: str) -> bool:
        if self.current_message_key == "hero_date_of_birth":
            try:
                datetime.strptime(value, "%d/%m/%Y")
            except ValueError:
                return False
        return True

    # TODO: WHAT IF CHAT EXPIRED BUT THE MESSAGE IS RECEIVED? PROCESS AS A START COMMAND BUT WITH ADDITIONAL
    #  EXPLANATIONS THAT THE CHAT IS EXPIRED
