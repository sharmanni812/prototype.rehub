from app import db_session
from app.tables import User  # подключение чертежа пользователя
import os

# 1. Подготовка: создание папки для базы, если ей нет
if not os.path.exists('db'):
    os.makedirs('db')
    print("Создана папка 'db'")

# 2. Инициализация базы данных
db_session.global_init("db/projects.db")

# 3. Открытие сесси (окно для работы с данными)
session = db_session.create_session()

# 4. Проверка есть ли уже что-то в базе, чтобы не было дубликатов
test_email = "your_email@example.com"
existing_user = session.query(User).filter(User.email == test_email).first()

if not existing_user:
    # СОЗДАНИЕ ПОЛЬЗОВАТЕЛЯ
    new_user = User()
    new_user.name = "Твое Имя"  # Напиши тут своё имя
    new_user.email = test_email
    new_user.skills = "Python, SQLAlchemy, Git"
    new_user.bio = "Разработчик платформы для поиска IT-команд"

    # Добавление в список на сохранение
    session.add(new_user)

    # Физическое записывание в файл .db
    session.commit()
    print("--- УСПЕХ: Пользователь добавлен в базу! ---")
else:
    print(f"--- ИНФО: Пользователь {existing_user.name} уже есть в базе ---")

# 5. ВЫВОД СПИСКА ВСЕХ ИЗ БАЗЫ
print("\nСПИСОК ПОЛЬЗОВАТЕЛЕЙ В ПРОЕКТЕ:")
all_users = session.query(User).all()

for u in all_users:
    print(f"ID: {u.id} | Имя: {u.name} | Почта: {u.email} | Навыки: {u.skills}")