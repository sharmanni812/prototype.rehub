from app import db_session
import os

# 1. Проверяем наличие папки для базы данных
if not os.path.exists('db'):
    os.makedirs('db')
    print("Папка 'db' создана.")

# 2. Инициализируем базу (вызываем твою функцию из db_session.py)
db_session.global_init("db/projects.db")

# 3. Пробуем открыть сессию
session = db_session.create_session()

if session:
    print("Статус: База данных 'projects.db' успешно инициализирована и готова к работе!")