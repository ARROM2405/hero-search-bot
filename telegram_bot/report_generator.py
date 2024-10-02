import datetime
import os.path

from django.conf import settings
from django.db.models import QuerySet

from telegram_bot.constants import DATE_FORMAT
from telegram_bot.models import HeroData


class ReportGenerator:
    def __init__(self, start_date: datetime.date, end_date: datetime.date):
        self.start_date = start_date
        self.end_date = end_date

    def _get_filter_date_times(self) -> tuple[datetime.datetime, datetime.datetime]:
        start_datetime = datetime.datetime.combine(self.start_date, datetime.time.min)
        end_datetime = datetime.datetime.combine(self.end_date, datetime.time.max)
        return start_datetime, end_datetime

    def _get_filtered_queryset(self) -> QuerySet:
        filter_date_times = self._get_filter_date_times()
        return (
            HeroData.objects.filter(created_at__range=filter_date_times)
            .order_by("-created_at")
            .iterator()
        )

    def _get_file_name(self) -> str:
        file_name = f"{self.start_date.strftime(DATE_FORMAT)}_{self.end_date.strftime(DATE_FORMAT)}.csv"
        file_path = os.path.join(settings.BASE_DIR, file_name)
        return file_path

    @staticmethod
    def _convert_hero_data_to_row(hero_data: HeroData) -> str:
        hero_full_name = f"{hero_data.hero_last_name} {hero_data.hero_first_name} {hero_data.hero_patronymic}"
        hero_date_of_birth = hero_data.hero_date_of_birth.strftime(DATE_FORMAT)
        relative_full_name = f"{hero_data.relative_last_name} {hero_data.relative_first_name} {hero_data.relative_patronymic}"
        if hero_data.is_added_to_dna_db:
            is_added_to_dna_db = "Так"
        else:
            is_added_to_dna_db = "Ні"
        created_at_date = hero_data.created_at.strftime(DATE_FORMAT)
        joined_data = ";".join(
            [
                hero_data.case_id,
                hero_full_name,
                hero_date_of_birth,
                hero_data.item_used_for_dna_extraction or "",
                is_added_to_dna_db,
                relative_full_name,
                hero_data.comment or "",
                created_at_date,
            ]
        )
        return f"{joined_data}\n"

    def generate_report(self):
        file_name = self._get_file_name()
        with open(file_name, "w") as report_file:
            headers_line = "Номер справи;ПІБ зниклого;Дата народження зниклого;Речі для отримання ДНК;Чи додано до бази ДНК;ПІБ родича;Коментар;Дата подання даних\n"
            report_file.write(headers_line)
            for hero_data in self._get_filtered_queryset():
                data_as_row = self._convert_hero_data_to_row(hero_data)
                report_file.write(data_as_row)
        return file_name
