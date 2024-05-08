from django.db import models


class DataEntryAuthor(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    first_name = models.CharField(max_length=100, blank=True, null=True)
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
    author = models.ForeignKey(to=DataEntryAuthor, on_delete=models.PROTECT)
