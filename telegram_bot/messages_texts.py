FIRST_INSTRUCTIONS = """
Привіт, я бот для передачі інформації по пошуку героя ЗСУ.
Я буду просити тебе по черзі відправляти мені дані.
В кінці буде можливість все перепровірити і, якщо необхідно,
відмінити прийняття надісланих даних і все відправити з самого початку."""

INQUERY_MESSAGE_START = "Будь ласка введіть "

CASE_ID_INQUERY = "номер справи в реєстрі."
HERO_FIRST_NAME_INQUERY = "ім'я героя."
HERO_LAST_NAME_INQUERY = "прізвище героя."
HERO_PATRONYMIC_NAME_INQUERY = "ім'я по батькові героя."
HERO_DATE_OF_BIRTH_INQUERY = (
    "дату народження героя в форматі ДД/ММ/РРРР, наприклад: 28/08/1990."
)
ITEM_USED_FOR_DNA_EXTRACTION_INQUERY = "предмет який використовували для отримання ДНК."
RELATIVE_FIRST_NAME_INQUERY = "ім'я родича."
RELATIVE_LAST_NAME_INQUERY = "прізвище родича."
RELATIVE_PATRONYMIC_NAME_INQUERY = "ім'я по батькову родича."
IS_ADDED_TO_DNA_DB_INQUERY = "чи доданий зразок ДНК до бази в форматі Так/Ні."
COMMENT_INQUERY = (
    "комментар, якщо потрібно. Якщо немає потреби додаткових коментарів, введіть Ні."
)

INPUT_CONFIRMED_RESPONSE = (
    "Дякую, ваші дані збереджені і будуть передані <link to the admin>."
)
INPUT_NOT_CONFIRMED_RESPONSE = (
    "Введені дані видалено. Я запрошу ввести ще раз усі дані як попередньо. "
)

ALL_DATA_RECEIVED_RESPONSE = (
    "Від вас отримані всі дані. Якщо це не так, будьласка зверніться до <link_to_admin>"
)
