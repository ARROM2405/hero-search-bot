from rest_framework import status
from rest_framework.exceptions import APIException


class AllDataReceivedException(Exception):
    def __init__(self):
        self.message = "All data is already received."


class TelegramMessageNotParsedException(Exception):
    def __init__(self):
        self.message = "Telegram message is not parsed yet."


class UnknownCommandException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Unknown command is passed by the user."
