from django.db import models
from enumfields.fields import EnumIntegerField

from telegram_bot.enums import UserActionType, ChatType


class TelegramUser(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    username = models.CharField(max_length=100, blank=True, null=True, unique=True)


class HeroData(models.Model):
    case_id = models.CharField(max_length=100)
    hero_last_name = models.CharField(max_length=100)
    hero_first_name = models.CharField(max_length=100)
    hero_patronymic = models.CharField(max_length=100)
    hero_date_of_birth = models.DateField()
    item_used_for_dna_extraction = models.CharField(
        max_length=100, blank=True, null=True
    )
    relative_last_name = models.CharField(max_length=100)
    relative_first_name = models.CharField(max_length=100)
    relative_patronymic = models.CharField(max_length=100)
    is_added_to_dna_db = models.BooleanField(default=False)
    comment = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(to=TelegramUser, on_delete=models.PROTECT)


class BotStatusChange(models.Model):
    initiator = models.ForeignKey(to=TelegramUser, on_delete=models.PROTECT)
    action_type = EnumIntegerField(UserActionType)
    chat_type = EnumIntegerField(ChatType)
    date_time = models.DateTimeField(auto_now_add=True)
    chat_id = models.BigIntegerField()
