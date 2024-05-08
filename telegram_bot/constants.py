import os
from typing import final

from dotenv import load_dotenv
from django.conf import settings

from telegram_bot.messages_texts import *

load_dotenv(os.path.join(settings.BASE_DIR, ".env"))

BASE_URL: final = f"https://api.telegram.org/bot{os.getenv('BOT_TOKEN')}/"

# TODO: create as enum
ORDER_OF_MESSAGES: final = [
    "case_id",
    "hero_last_name",
    "hero_first_name",
    "hero_patronymic",
    "hero_date_of_birth",
    "item_used_for_dna_extraction",
    "relative_last_name",
    "relative_first_name",
    "relative_patronymic",
    "is_added_to_dna_db",
    "comment",
]

MESSAGES_MAPPING: final = {
    "case_id": INQUERY_MESSAGE_START + CASE_ID_INQUERY,
    "hero_last_name": INQUERY_MESSAGE_START + HERO_LAST_NAME_INQUERY,
    "hero_first_name": INQUERY_MESSAGE_START + HERO_FIRST_NAME_INQUERY,
    "hero_patronymic": INQUERY_MESSAGE_START + HERO_PATRONYMIC_NAME_INQUERY,
    "hero_date_of_birth": INQUERY_MESSAGE_START + HERO_DATE_OF_BIRTH_INQUERY,
    "item_used_for_dna_extraction": INQUERY_MESSAGE_START
    + ITEM_USED_FOR_DNA_EXTRACTION_INQUERY,
    "relative_last_name": INQUERY_MESSAGE_START + RELATIVE_LAST_NAME_INQUERY,
    "relative_first_name": INQUERY_MESSAGE_START + RELATIVE_FIRST_NAME_INQUERY,
    "relative_patronymic": INQUERY_MESSAGE_START + RELATIVE_PATRONYMIC_NAME_INQUERY,
    "is_added_to_dna_db": INQUERY_MESSAGE_START + IS_ADDED_TO_DNA_DB_INQUERY,
    "comment": INQUERY_MESSAGE_START + COMMENT_INQUERY,
}
