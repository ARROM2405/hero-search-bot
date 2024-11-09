from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from telegram_bot.logger_config import logger
from telegram_bot.message_handling_services import MessageHandler
from telegram_bot.serializers import TelegramBotSerializer


class TelegramBotApiView(GenericViewSet):
    serializer_class = TelegramBotSerializer

    @logger.catch
    @action(methods=["POST"], detail=False)
    def user_message(self, request):
        logger.info(f"Received request with data: {request.data}")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        handler = MessageHandler(telegram_message=self.request.data)
        handler.handle_telegram_message()
        return Response(status=status.HTTP_200_OK)
