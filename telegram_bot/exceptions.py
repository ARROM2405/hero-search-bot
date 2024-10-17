from rest_framework import status
from rest_framework.exceptions import APIException


class AllDataReceivedException(Exception):
    def __init__(self):
        self.message = "All data is already received."


class TelegramMessageNotParsedException(Exception):
    def __init__(self):
        self.message = "Telegram message is not parsed yet."


class UnknownCommandException(Exception):
    def __init__(self):
        self.message = "Unknown command is passed by the user."


class UnauthorizedUserCalledReportGenerationException(Exception):
    def __init__(self, message="Unauthorized user called for report generation."):
        self.message = message
