from app import db_session, services
from app.tables import User, Project, Application
import os

# Инициализация
db_session.global_init("db/projects.db")
session = db_session.create_session()
current_user = session.query(User).first()

# --- ФУНКЦИИ-ОБРАБОТЧИКИ ---

def check_new_alerts():
    """Проверка новых статусов при входе в меню"""
    if not current_user: return
    
    # Считаем принятые и отклоненные, чтобы не спамить списком, а просто намекнуть
    accepted = session.query(Application).filter(Application.user_id == current_user.id, Application.status == "Принят").count()
    rejected = session.query(Application).filter(Application.user_id == current_user.id, Application.status == "Отклонен").count()
    
    if accepted > 0 or rejected > 0:
        print(f"\n🔔 У вас есть обновления по откликам ({accepted} прир. / {rejected} откл.). Загляните в пункт 6!")

def show_projects():
    print("\n" + "="*20 + "\nВЫБЕРИТЕ НАПРАВЛЕНИЕ:\n1. IT\n2. Media\n3. Fashion\n0. Назад")
    cat_choice = input("\nВыбор темы: ")
    categories = {"1": "IT", "2": "Media", "3": "Fashion"}
    selected_cat = categories.get(cat_choice)
    
    if selected_cat:
        projects = services.get_projects_by_category(session, selected_cat)
        print(f"\n--- ПРОЕКТЫ: {selected_cat.upper()} ---")
        if not projects: print("Пусто.")
        else:
            for p in projects: print(f"[{p.id}] {p.title}")
            did = input("\nID для подробностей (0 - назад): ")
            if did != "0":
                proj = session.get(Project, did)
                if proj:
                    print(f"\n--- {proj.title} ---\nАвтор: {proj.user.name}\nОписание: {proj.description}\nНужны: {proj.needed_roles}\n" + "-"*25)
                    input("Enter...")

def create_project():
    if not current_user: return print("Войдите в систему!")
    print("\n--- НОВЫЙ ПРОЕКТ ---")
    t, d = input("Название: "), input("Описание: ")
    c = input("Категория (IT/Media/Fashion): ").strip()
    r = input("Кто нужен: ")
    services.create_project(session, t, d, current_user.id, c, r)
    print("Проект создан!")

def register_user():
    global current_user
    n, e = input("Имя: "), input("Email: ")
    current_user = services.create_user(session, n, e)
    print(f"Готово! Ваш ID: {current_user.id}")

def login():
    global current_user
    uid = input("Введите ваш ID: ")
    user = session.get(User, uid)
    if user:
        current_user = user
        print(f"Привет, {user.name}!")
    else: print("Не найден.")

def apply_to_project():
    if not current_user: return print("Войдите в систему!")
    pid = input("ID проекта для отклика: ")
    msg = input("Сообщение лидеру: ")
    if services.apply_to_project(session, current_user.id, pid, msg):
        print("Отклик отправлен!")
    else: print("Ошибка (возможно, это ваш проект).")

def show_my_outbox():
    """ИСХОДЯЩИЕ: Мои заявки в чужие проекты"""
    if not current_user: return print("Войдите в систему!")
    # Ищем все заявки, которые подал текущий юзер
    my_apps = session.query(Application).filter(Application.user_id == current_user.id).all()
    
    print("\n=== МОИ ОТКЛИКИ (КУДА Я ПОДАЛСЯ) ===")
    if not my_apps:
        print("Вы еще никуда не откликались.")
    else:
        for a in my_apps:
            status_icon = "⏳" if a.status == "Ожидание" else "✅" if a.status == "Принят" else "❌"
            print(f"{status_icon} Проект: {a.project.title}")
            print(f"   Статус: {a.status} | Ваше сообщение: {a.message}")
            print("-" * 20)
    input("\nНажмите Enter...")

def manage_my_projects_inbox():
    """ВХОДЯЩИЕ: Управление моими проектами и заявками в них"""
    if not current_user: return print("Войдите в систему!")
    my_projs = services.get_my_projects(session, current_user.id)
    
    if not my_projs: return print("\nУ вас нет своих проектов.")

    print("\n=== МОИ ПРОЕКТЫ И ЗАЯВКИ В НИХ ===")
    for p in my_projs:
        # Считаем сколько новых заявок на каждый проект
        count = session.query(Application).filter(Application.project_id == p.id, Application.status == "Ожидание").count()
        print(f"[{p.id}] {p.title} (Категория: {p.category}) — Новых заявок: {count}")
    
    pid = input("\nВыберите ID проекта для управления (0 - назад): ")
    if pid == "0": return

    project = session.get(Project, pid)
    if not project or project.leader_id != current_user.id: return print("Нет доступа.")

    print(f"\nПроект: {project.title}\n1. Посмотреть заявки\n2. Удалить проект\n0. Назад")
    act = input("Выбор: ")

    if act == "1":
        apps = services.get_project_applications(session, pid)
        for a in apps:
            print(f"\nID заявки: [{a.id}] | От: {a.user.name} | Статус: {a.status}\nТекст: {a.message}")
        
        aid = input("\nID заявки для решения (0 - назад): ")
        if aid != "0":
            res = input("1. Принять | 2. Отклонить: ")
            new_status = "Принят" if res == "1" else "Отклонен"
            services.update_application_status(session, aid, new_status)
            print("Статус обновлен!")
    elif act == "2":
        if input("Удалить? (y/n): ") == "y":
            services.delete_project(session, pid)
            print("Удалено.")

# --- ГЛАВНЫЙ ЦИКЛ ---

menu_actions = {
    "1": show_projects,
    "2": create_project,
    "3": register_user,
    "4": login,
    "5": apply_to_project,
    "6": show_my_outbox,           # Исходящие
    "7": manage_my_projects_inbox  # Входящие
}

while True:
    u_name = current_user.name if current_user else "Гость"
    print(f"\n{'='*35}\nREHUB | Пользователь: {u_name}\n{'='*35}")
    check_new_alerts()
    
    print("1. Найти проект")
    print("2. Создать проект")
    print("3. Регистрация / 4. Вход")
    print("5. Откликнуться")
    print("6. Мои отклики (ИСХОДЯЩИЕ)")
    print("7. Управление проектами (ВХОДЯЩИЕ)")
    print("8. Выход")
    
    choice = input("\nВыбор: ")
    if choice == "8": break
    action = menu_actions.get(choice)
    if action: action()