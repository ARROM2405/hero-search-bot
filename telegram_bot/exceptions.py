class AllDataReceivedException(Exception):
    def __init__(self):
        self.message = "All data is already received."


class TelegramMessageNotParsedException(Exception):
    def __init__(self):
        self.message = "Telegram message is not parsed yet."
