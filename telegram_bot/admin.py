from django.contrib import admin

from telegram_bot.models import TelegramUser, HeroData


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "telegram_id",
        "first_name",
        "last_name",
        "username",
    )
    list_filter = ("telegram_id",)
    search_fields = (
        "telegram_id",
        "first_name",
        "last_name",
        "username",
    )


@admin.register(HeroData)
class HeroDataAdmin(admin.ModelAdmin):
    list_display = (
        "case_id",
        "hero_last_name",
        "hero_first_name",
        "hero_patronymic",
        "hero_date_of_birth",
        "relative_last_name",
        "relative_first_name",
        "relative_patronymic",
        "is_added_to_dna_db",
        "author",
    )

    search_fields = (
        "case_id",
        "hero_last_name",
        "hero_first_name",
        "hero_patronymic",
        "hero_date_of_birth",
        "relative_last_name",
        "relative_first_name",
        "relative_patronymic",
        "author",
    )

    raw_id_fields = ("author",)
