from app import db_session, services
from app.tables import User, Project
import os

# Инициализация
db_session.global_init("db/projects.db")
session = db_session.create_session()
current_user = session.query(User).first()

# --- ФУНКЦИИ-ОБРАБОТЧИКИ ---

def show_projects():
    projects = services.get_all_projects(session)
    print("\n" + "="*20 + "\nСПИСОК ПРОЕКТОВ")
    for p in projects:
        print(f"[{p.id}] {p.title} ({p.category})")
    
    did = input("\nID для подробностей (0 - назад): ")
    if did != "0":
        proj = session.get(Project, did)
        if proj:
            print(f"\n--- {proj.title} ---\nАвтор: {proj.user.name}\nОписание: {proj.description}\nРоли: {proj.needed_roles}")
        else:
            print("Не найдено.")

def create_project():
    if not current_user: return print("Войдите в систему!")
    t, d = input("Название: "), input("Описание: ")
    c, r = input("Категория: "), input("Роли: ")
    services.create_project(session, t, d, current_user.id, c, r)
    print("Успешно создано!")

def register_user():
    global current_user
    n, e = input("Имя: "), input("Email: ")
    b, s = input("О себе: "), input("Навыки: ")
    current_user = services.create_user(session, n, e, b, s)
    print(f"Пользователь {n} готов!")

def login():
    global current_user
    uid = input("Введите ваш ID: ")
    user = session.get(User, uid)
    if user:
        current_user = user
        print(f"Привет, {user.name}!")
    else:
        print("Пользователь не найден.")

def apply_to_project():
    if not current_user: return print("Войдите в систему!")
    pid = input("ID проекта: ")
    project = session.get(Project, pid)
    if project and project.leader_id != current_user.id:
        msg = input("Сообщение: ")
        services.apply_to_project(session, current_user.id, pid, msg)
        print("Отклик отправлен!")
    else:
        print("Ошибка: проект не найден или он ваш.")

def show_notifications():
    if not current_user: return print("Войдите в систему!")
    apps = services.get_user_notifications(session, current_user.id)
    print("\n--- УВЕДОМЛЕНИЯ ---")
    for a in apps:
        print(f"Проект [{a.project.title}] -> от {a.user.name}: {a.message}")

# --- ГЛАВНЫЙ ЦИКЛ ---

# Словарь связывает цифру с функцией
menu_actions = {
    "1": show_projects,
    "2": create_project,
    "3": register_user,
    "4": login,
    "5": apply_to_project,
    "6": show_notifications
}

while True:
    user_status = f"{current_user.name} (ID: {current_user.id})" if current_user else "НЕ АВТОРИЗОВАН"
    print(f"\n{'='*20}\nВХОД: {user_status}\n{'='*20}")
    print("1. Проекты | 2. Создать | 3. Рега | 4. Вход | 5. Отклик | 6. Уведомления | 7. Выход")
    
    choice = input("\nВыбор: ")
    
    if choice == "7":
        print("Пока!")
        break
    
    # Вызываем функцию из словаря. Если цифры нет - ничего не делаем.
    action = menu_actions.get(choice)
    if action:
        action()
    else:
        print("Неверный ввод.")