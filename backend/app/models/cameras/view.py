from datetime import datetime
from sqladmin import ModelView
from app.models.cameras.model import Cameras

class CamerasView(ModelView, model=Cameras):
    # Названия на узбекском
    name = "Kamera"
    name_plural = "Kameralar"
    icon = "fa-solid fa-video"

    # 1. Список колонок для главной таблицы (скрываем даты здесь, если хотите)
    column_list = [
        "id",
        "device_ip",
        "username",
        "direction",
        "is_active",
    ]

    # 2. Список колонок для детального просмотра (здесь даты БУДУТ видны)
    column_details_list = [
        "id",
        "device_ip",
        "username",
        "password",
        "direction",
        "is_active",
        "created_at",
        "updated_at",
    ]

    # Перевод на узбекский
    column_labels = {
        "id": "ID",
        "device_ip": "Qurilma IP manzili",
        "username": "Foydalanuvchi nomi",
        "password": "Parol",
        "direction": "Yo'nalish",
        "is_active": "Holati (Aktiv)",
        "created_at": "Yaratilgan vaqti",
        "updated_at": "Tahrirlangan vaqti",
    }

    # 3. Красивое форматирование времени (User Friendly)
    # Выводит дату в формате: 28.02.2026 22:15
    column_formatters = {
        "created_at": lambda m, a: m.created_at.strftime("%d.%m.%Y %H:%M") if m.created_at else "",
        "updated_at": lambda m, a: m.updated_at.strftime("%d.%m.%Y %H:%M") if m.updated_at else "",
    }

    # Поля для поиска
    column_searchable_list = ["device_ip", "username"]

    # Исключаем даты из форм создания/редактирования
    form_excluded_columns = ["created_at", "updated_at", "id", "events"]

    # Поля, которые можно заполнять
    form_columns = ["device_ip", "username", "password", "direction", "is_active"]

    # 4. Очистка пробелов (strip)
    async def on_model_change(self, data, model, is_created):
        for key, value in data.items():
            if isinstance(value, str):
                data[key] = value.strip()
        return await super().on_model_change(data, model, is_created)