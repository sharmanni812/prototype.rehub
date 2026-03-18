from app import db_session, services
from app.tables import User, Project
import os

# Инициализация
db_session.global_init("db/projects.db")
session = db_session.create_session()
current_user = session.query(User).first()

# --- ФУНКЦИИ-ОБРАБОТЧИКИ ---

def show_projects():
    """Подменю выбора категорий"""
    print("\n" + "="*20)
    print("ВЫБЕРИТЕ НАПРАВЛЕНИЕ:")
    print("1. IT")
    print("2. Media")
    print("3. Fashion")
    print("0. Назад")
    
    cat_choice = input("\nВыбор темы: ")
    
    # Словарь для быстрого подбора категории
    categories = {"1": "IT", "2": "Media", "3": "Fashion"}
    selected_cat = categories.get(cat_choice)
    
    if selected_cat:
        # Используем новую функцию фильтрации из services
        projects = services.get_projects_by_category(session, selected_cat)
        print(f"\n--- ПРОЕКТЫ В СФЕРЕ {selected_cat.upper()} ---")
        
        if not projects:
            print("В этой категории пока пусто.")
        else:
            for p in projects:
                print(f"[{p.id}] {p.title}")
            
            did = input("\nID для подробностей (0 - назад): ")
            if did != "0":
                proj = session.get(Project, did)
                if proj:
                    print(f"\n--- ПОДРОБНОСТИ: {proj.title} ---")
                    print(f"Автор: {proj.user.name}")
                    print(f"Описание: {proj.description}")
                    print(f"Ищут в команду: {proj.needed_roles}")
                    print("-" * 25)
                    input("Нажмите Enter, чтобы вернуться...")
                else:
                    print("Проект не найден.")
    elif cat_choice != "0":
        print("Неверный ввод.")

def create_project():
    if not current_user: return print("Войдите в систему!")
    
    print("\n--- НОВЫЙ ПРОЕКТ ---")
    t = input("Название: ")
    d = input("Описание: ")
    
    print("Доступные темы: IT, Media, Fashion")
    c = input("Категория: ").strip()
    
    # Авто-коррекция регистра
    if c.lower() == 'it': c = 'IT'
    elif c.lower() == 'media': c = 'Media'
    elif c.lower() == 'fashion': c = 'Fashion'
    
    r = input("Кто нужен (роли): ")
    
    # services.create_project сам проверит, входит ли 'c' в список разрешенных
    services.create_project(session, t, d, current_user.id, c, r)
    print(f"Проект успешно создан в разделе {c}!")

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
    pid = input("ID проекта для отклика: ")
    project = session.get(Project, pid)
    
    if project:
        if project.leader_id == current_user.id:
            print("Нельзя откликаться на свой проект.")
        else:
            msg = input("Сообщение лидеру: ")
            services.apply_to_project(session, current_user.id, pid, msg)
            print("Отклик отправлен!")
    else:
        print("Проект не найден.")

def show_notifications():
    if not current_user: return print("Войдите в систему!")
    apps = services.get_user_notifications(session, current_user.id)
    print("\n--- ВХОДЯЩИЕ ЗАЯВКИ ---")
    if not apps:
        print("У вас пока нет уведомлений.")
    else:
        for a in apps:
            print(f"Проект [{a.project.title}]")
            print(f"От: {a.user.name} | Сообщение: {a.message}")
            print("-" * 20)
    input("Нажмите Enter...")

# --- ГЛАВНЫЙ ЦИКЛ ---

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
    print(f"\n{'='*30}\nREHUB: {user_status}\n{'='*30}")
    print("1. Проекты по темам")
    print("2. Создать проект")
    print("3. Регистрация")
    print("4. Сменить пользователя")
    print("5. Откликнуться")
    print("6. Уведомления")
    print("7. Выход")
    
    choice = input("\nВыбор (1-7): ")
    
    if choice == "7":
        print("До встречи!")
        break
    
    action = menu_actions.get(choice)
    if action:
        action()
    else:
        print("Неверный ввод.")