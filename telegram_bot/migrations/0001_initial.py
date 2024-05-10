# Generated by Django 5.0.3 on 2024-05-08 12:39

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="DataEntryAuthor",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("telegram_id", models.BigIntegerField(unique=True)),
                ("first_name", models.CharField(max_length=100)),
                ("last_name", models.CharField(blank=True, max_length=100, null=True)),
                (
                    "username",
                    models.CharField(
                        blank=True, max_length=100, null=True, unique=True
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="HeroData",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("case_id", models.CharField(max_length=100)),
                ("hero_last_name", models.CharField(max_length=100)),
                ("hero_first_name", models.CharField(max_length=100)),
                ("hero_patronymic", models.CharField(max_length=100)),
                ("hero_date_of_birth", models.DateField()),
                (
                    "item_used_for_dna_extraction",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                ("relative_last_name", models.CharField(max_length=100)),
                ("relative_first_name", models.CharField(max_length=100)),
                ("relative_patronymic", models.CharField(max_length=100)),
                ("is_added_to_dna_db", models.BooleanField(default=False)),
                ("comment", models.TextField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "author",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="telegram_bot.dataentryauthor",
                    ),
                ),
            ],
        ),
    ]
