import os

import telegram
from dotenv import load_dotenv

from oshb_data_collection.settings import BASE_DIR

load_dotenv(os.path.join(BASE_DIR, ".env"))
token = os.getenv("LONG_POLLING_BOT_TOKEN")

bot = telegram.Bot(token)
