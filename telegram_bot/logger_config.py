import os.path

from django.utils.timezone import now
from loguru import logger

from hero_search_bot.settings import LOGS_DIRECTORY

logger.add(
    os.path.join(LOGS_DIRECTORY, f"log_{now().date()}.log"),
    rotation="1 day",
    retention="1 week",
)
