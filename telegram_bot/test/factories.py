from datetime import date

import factory

from telegram_bot.models import HeroData, TelegramUser


class TelegramUserFactory(factory.django.DjangoModelFactory):
    telegram_id = factory.Sequence(lambda n: n)
    first_name = factory.Sequence(lambda n: f"first_name_{n}")
    last_name = factory.Sequence(lambda n: f"last_name_{n}")
    username = factory.Sequence(lambda n: f"username_{n}")

    class Meta:
        model = TelegramUser


class HeroDataFactory(factory.django.DjangoModelFactory):
    case_id = factory.Sequence(lambda n: f"case_id_{n}")
    hero_last_name = factory.Sequence(lambda n: f"hero_ln_{n}")
    hero_first_name = factory.Sequence(lambda n: f"hero_fn_{n}")
    hero_patronymic = factory.Sequence(lambda n: f"hero_p_{n}")
    hero_date_of_birth = date(year=1990, month=1, day=2)
    relative_last_name = factory.Sequence(lambda n: f"relative_ln_{n}")
    relative_first_name = factory.Sequence(lambda n: f"relative_fn_{n}")
    relative_patronymic = factory.Sequence(lambda n: f"relative_p_{n}")
    author = factory.SubFactory(TelegramUserFactory)

    class Meta:
        model = HeroData

