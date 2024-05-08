from rest_framework import routers

from telegram_bot.api import TelegramBotApiView

router = routers.DefaultRouter()
router.register(r'telegram_bot', TelegramBotApiView, basename='telegram_bot')

urlpatterns = router.urls