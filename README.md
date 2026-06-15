# Cook-Recipes
# 1. Клонировать репозиторий или скачать проект архивом.
# 2. Создать виртуальное окружение (python -m venv venv), потом активировать его (venv\Scripts\activate) 
# 3. Установить зависимости (pip install -r requirements.txt)
# 4. Установить MySQL 9.7 и создать базу данных
В MySQL выполнить:
CREATE DATABASE cook_recipes
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
# 5. Создать файл `.env`
Скопировать файл .env.example и создать файл .env.
# 6. Перейти в папку backend (cd backend) 
# 7. Применить миграции (только при первом запуске) - alembic upgrade head
# 8. Заполнить базу тестовыми данными (только при первом запуске) - python seed_data.py
# 9. Запустить сервер (uvicorn main:app --reload). После запуска приложение будет доступно.

# При последующих запусках достаточно выполнить: cd cook-recipes, venv\Scripts\activate, cd backend, uvicorn main:app --reload.
