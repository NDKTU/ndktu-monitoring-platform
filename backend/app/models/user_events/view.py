from datetime import datetime
from sqladmin import ModelView
from app.models.user_events.model import UserEvents

class UserEventsView(ModelView, model=UserEvents):
    # Названия на узбекском
    name = "Foydalanuvchi hodisasi"
    name_plural = "Foydalanuvchi hodisalari"
    icon = "fa-solid fa-calendar-check"  # Исправленная иконка (events)

    # Список колонок в таблице
    column_list = [
        "id",
        "user",
        "camera",
        "enter_time",
        "exit_time",
    ]

    # Детальный просмотр (включаем даты создания/обновления здесь)
    column_details_list = [
        "id",
        "user",
        "camera",
        "enter_time",
        "exit_time",
    ]

    # Перевод на узбекский (Label)
    column_labels = {
        "id": "ID",
        "user": "Foydalanuvchi",
        "camera": "Kamera",
        "enter_time": "Kirish vaqti",
        "exit_time": "Chiqish vaqti",
    }

    # Поиск
    column_searchable_list = ["user", "camera"]

    # Форматирование времени для всех полей с датами
    column_formatters = {
        "enter_time": lambda m, a: m.enter_time.strftime("%d.%m.%Y %H:%M") if m.enter_time else "",
        "exit_time": lambda m, a: m.exit_time.strftime("%d.%m.%Y %H:%M") if m.exit_time else "",
    }

    # Исключаем системные поля из форм
    form_excluded_columns = ["id"]

    # Поля для редактирования
    form_columns = [
        "user",
        "camera",
        "enter_time",
        "exit_time",
    ]

    # Очистка пробелов (strip)
    async def on_model_change(self, data, model, is_created):
        for key, value in data.items():
            if isinstance(value, str):
                data[key] = value.strip()
        return await super().on_model_change(data, model, is_created)