<<<<<<< HEAD
# ИнструментДрайв — Django-проект

Маркетплейс аренды и продажи строительного инструмента. У каждой категории свои характеристики, фильтры строятся по ним автоматически (как параметры на auto.ru).

## Запуск
```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
python manage.py makemigrations market
python manage.py migrate
python manage.py seed                 # демо-данные, пользователь demo / demo12345
python manage.py createsuperuser      # для админки
python manage.py runserver
```
Сайт: http://127.0.0.1:8000/  Админка: http://127.0.0.1:8000/admin/

## Как это устроено
- `Category` → `AttributeDef` (характеристики: список, число или текст, с единицей измерения) → `ListingValue` (значения у объявления).
- **Новая категория или характеристика добавляется в админке без изменения кода**: форма подачи и фильтры подстроятся сами.
- Авторизация встроенная Django: регистрация, вход, выход. Контакты и заявки доступны только вошедшим.
- Дополнительно: фото, заявки на аренду с датами, личный кабинет, поиск, сортировка, пагинация, скрытие объявления.

## Структура
- `config/` настройки и корневые URL
- `market/models.py`, `forms.py`, `views.py`, `urls.py`, `admin.py`
- `market/management/commands/seed.py` демо-данные
- `market/templates/`, `market/static/market/style.css`

## Что дальше
Проверка пересечения дат аренды, залог, отзывы, оплата, PostgreSQL и сборка статики для продакшена (`DEBUG=0`, `SECRET_KEY`, `ALLOWED_HOSTS` через переменные окружения).
