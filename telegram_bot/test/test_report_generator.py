import datetime
import os.path
from unittest import mock

from django.conf import settings
from django.test import TestCase
from django.utils.timezone import now
from precisely import assert_that, is_sequence

from telegram_bot.constants import DATE_FORMAT
from telegram_bot.report_generator import ReportGenerator
from telegram_bot.test.factories import TelegramUserFactory, HeroDataFactory


class TestReportGenerator(TestCase):
    def setUp(self):
        self.telegram_user_1 = TelegramUserFactory()
        self.telegram_user_2 = TelegramUserFactory()

        self.hero_data_1 = HeroDataFactory(author=self.telegram_user_1)
        self.hero_data_2 = HeroDataFactory(author=self.telegram_user_1)
        self.hero_data_3 = HeroDataFactory(author=self.telegram_user_2)

        self.hero_data_1.created_at = now() - datetime.timedelta(days=2)
        self.hero_data_1.save()
        self.hero_data_2.created_at = now() - datetime.timedelta(days=1)
        self.hero_data_2.save()

    def test_get_filter_date_times(self):
        test_date = datetime.date(year=2024, month=2, day=1)
        filter_date_times = ReportGenerator(
            test_date,
            test_date,
        )._get_filter_date_times()
        assert_that(
            filter_date_times,
            is_sequence(
                datetime.datetime(
                    year=2024,
                    month=2,
                    day=1,
                    hour=0,
                    minute=0,
                ),
                datetime.datetime(
                    year=2024,
                    month=2,
                    day=1,
                    hour=23,
                    minute=59,
                    second=59,
                    microsecond=999999,
                ),
            ),
        )

    @mock.patch("telegram_bot.report_generator.ReportGenerator._get_filter_date_times")
    def test_get_filtered_queryset(self, mock_get_filter_date_times):
        mock_get_filter_date_times.return_value = (
            datetime.datetime.combine(date=now(), time=datetime.time.min)
            - datetime.timedelta(days=1),
            datetime.datetime.combine(date=now(), time=datetime.time.max),
        )
        returned_objects_list = list(
            ReportGenerator(
                now()
                - datetime.timedelta(
                    days=2,
                ),
                now(),
            )._get_filtered_queryset()
        )
        assert_that(
            returned_objects_list,
            is_sequence(
                self.hero_data_3,
                self.hero_data_2,
            ),
        )

    def test_get_file_name(self):
        test_date = datetime.date(year=2024, month=2, day=1)
        assert ReportGenerator(test_date, test_date)._get_file_name() == os.path.join(
            settings.BASE_DIR, "01-02-2024_01-02-2024.csv"
        )

    def test_convert_hero_data_to_row(self):
        self.hero_data_1.created_at = datetime.datetime(
            year=2024, month=1, day=2, hour=12
        )
        self.hero_data_1.save()
        hero_full_name = f"{self.hero_data_1.hero_last_name} {self.hero_data_1.hero_first_name} {self.hero_data_1.hero_patronymic}"
        hero_date_of_birth = self.hero_data_1.hero_date_of_birth.strftime(DATE_FORMAT)
        relative_full_name = f"{self.hero_data_1.relative_last_name} {self.hero_data_1.relative_first_name} {self.hero_data_1.relative_patronymic}"
        created_at_date = self.hero_data_1.created_at.strftime(DATE_FORMAT)

        assert (
            ReportGenerator._convert_hero_data_to_row(self.hero_data_1)
            == f"{self.hero_data_1.case_id};{hero_full_name};{hero_date_of_birth};;Ні;{relative_full_name};;{created_at_date}\n"
        )

    @mock.patch("telegram_bot.report_generator.ReportGenerator._get_filtered_queryset")
    def test_generate_report(self, mock_get_filtered_queryset):
        mock_get_filtered_queryset.return_value = (
            hero_data
            for hero_data in (
                self.hero_data_3,
                self.hero_data_2,
            )
        )
        start_date = now().date() - datetime.timedelta(days=2)
        end_date = now().date()
        report_generator = ReportGenerator(
            start_date=start_date,
            end_date=end_date,
        )
        report_file_path = report_generator.generate_report()
        with open(report_file_path, "r") as generated_report:
            lines = generated_report.readlines()

        assert len(lines) == 3
        assert lines[0].split(";")[0] == "Номер справи"
        assert lines[1].split(";")[0] == self.hero_data_3.case_id
        assert lines[2].split(";")[0] == self.hero_data_2.case_id

        os.remove(report_file_path)
