from sqladmin import ModelView
from app.models.users.model import User

class UserView(ModelView, model=User):
    # Номланиши (Названия)
    name = "Foydalanuvchi"
    name_plural = "Foydalanuvchilar"
    icon = "fa-solid fa-user-gear"

    # Рўйхатда кўринадиган устунлар (Пароль яширилган)
    column_list = [
        "id",
        "username",
        "is_active",
        "in_work",
    ]

    # Батафсил маълумот (Detail) - ҳаммаси кўринади
    column_details_list = [
        "id",
        "username",
        "password",
        "is_active",
        "in_work",
        "created_at",
        "updated_at",
    ]

    # Таржималар (Labels)
    column_labels = {
        "id": "ID",
        "username": "Foydalanuvchi nomi",
        "password": "Parol",
        "is_active": "Aktiv",
        "in_work": "Ish jarayonida",
        "created_at": "Yaratilgan vaqti",
        "updated_at": "Tahrirlangan vaqti",
    }

    # Қидирув
    column_searchable_list = ["username"]

    # Вақтни чиройли форматда кўрсатиш
    column_formatters = {
        "created_at": lambda m, a: m.created_at.strftime("%d.%m.%Y %H:%M") if m.created_at else "",
        "updated_at": lambda m, a: m.updated_at.strftime("%d.%m.%Y %H:%M") if m.updated_at else "",
    }

    # Формадан тизимли устунларни олиб ташлаш
    form_excluded_columns = [
        "created_at", 
        "updated_at", 
        "id"
    ]

    # Тўлдириладиган майдонлар
    form_columns = [
        "username",
        "password",
        "is_active",
        "in_work",
    ]

    # Маълумотни сақлашдан олдин пробелларни тозалаш (strip)
    async def on_model_change(self, data, model, is_created):
        """
        Username ва Parol каби матнли майдонлардаги 
        ортиқcha пробелларни олиб ташлайди.
        """
        for key, value in data.items():
            if isinstance(value, str):
                data[key] = value.strip()
        
        return await super().on_model_change(data, model, is_created)