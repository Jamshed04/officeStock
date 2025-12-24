#!/bin/sh
# Применяем миграции
alembic upgrade head

# Запускаем приложение
uvicorn main:main_app --host 0.0.0.0 --port 8045
