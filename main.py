from app import db_session, services
from app.tables import User, Project, Application
import os

# Инициализация
db_session.global_init("db/projects.db")
session = db_session.create_session()
current_user = session.query(User).first()

# --- ФУНКЦИИ-ОБРАБОТЧИКИ (ИНТЕРФЕЙС) ---

def check_new_alerts():
    """Проверка уведомлений о статусах заявок"""
    if not current_user: return
    
    accepted = session.query(Application).filter(
        Application.user_id == current_user.id, 
        Application.status == "Принят"
    ).count()
    rejected = session.query(Application).filter(
        Application.user_id == current_user.id, 
        Application.status == "Отклонен"
    ).count()
    
    if accepted > 0 or rejected > 0:
        print(f"\n🔔 УВЕДОМЛЕНИЕ: +{accepted} принятых / +{rejected} отклоненных откликов.")
        print("Подробности в пункте 6.")

def show_projects():
    print("\n" + "="*20 + "\nНАПРАВЛЕНИЯ:\n1. IT\n2. Media\n3. Fashion\n0. Назад")
    choice = input("\nВыбор темы: ")
    cats = {"1": "IT", "2": "Media", "3": "Fashion"}
    selected = cats.get(choice)
    
    if selected:
        projects = services.get_projects_by_category(session, selected)
        print(f"\n--- ПРОЕКТЫ: {selected.upper()} ---")
        if not projects: print("Пока пусто.")
        else:
            for p in projects:
                status = "[НАБОР]" if p.needed_roles != "КОМАНДА СОБРАНА" else "[ЗАКРЫТ]"
                print(f"[{p.id}] {status} {p.title}")
            
            pid = input("\nID проекта для деталей (0 - назад): ")
            if pid != "0":
                proj = session.get(Project, pid)
                if proj:
                    print(f"\n--- {proj.title} ---\nАвтор: {proj.user.name}\nОписание: {proj.description}")
                    team = services.get_project_team(session, proj.id)
                    if team:
                        print(f"В команде: {', '.join([u.name for u in team])}")
                    input("\nEnter...")

def create_project():
    if not current_user: return print("Войдите в систему!")
    print("\n--- СОЗДАНИЕ ПРОЕКТА ---")
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
    else: print("Ошибка.")

def show_my_outbox():
    if not current_user: return print("Войдите в систему!")
    my_apps = session.query(Application).filter(Application.user_id == current_user.id).all()
    print("\n=== МОИ ОТКЛИКИ (ИСХОДЯЩИЕ) ===")
    for a in my_apps:
        icon = "⏳" if a.status == "Ожидание" else "✅" if a.status == "Принят" else "❌"
        print(f"{icon} Проект: {a.project.title} | Статус: {a.status}")
    input("\nEnter...")

def manage_my_projects_center():
    if not current_user: return print("Войдите в систему!")
    
    as_leader = services.get_my_projects(session, current_user.id)
    as_member = services.get_projects_i_am_in(session, current_user.id)
    
    print("\n=== ВАШИ ПРОЕКТЫ ===")
    if as_leader:
        for p in as_leader: print(f"[{p.id}] {p.title} (ЛИДЕР)")
    if as_member:
        for p in as_member: print(f"[{p.id}] {p.title} (УЧАСТНИК)")

    pid = input("\nID проекта (0 - назад): ")
    if pid == "0": return
    project = session.get(Project, pid)

    if project and project.leader_id == current_user.id:
        print(f"\n1. Заявки\n2. Команда\n3. Завершить набор\n4. Удалить проект")
        act = input("Выбор: ")
        if act == "1":
            apps = services.get_project_applications(session, pid)
            for a in apps: print(f"[{a.id}] {a.user.name}: {a.message}")
            aid = input("\nID заявки (0 - назад): ")
            if aid != "0":
                res = input("1. Принять | 2. Отклонить: ")
                services.update_application_status(session, aid, "Принят" if res == "1" else "Отклонен")
        elif act == "2":
            team = services.get_project_team(session, pid)
            for m in team: print(f"- {m.name} ({m.email})")
            input("\nEnter...")
        elif act == "3":
            services.close_project(session, pid)
        elif act == "4":
            services.delete_project(session, pid)
    elif project:
        print(f"\nПроект: {project.title}. Вы участник команды.")
        input("Enter...")

def delete_my_account():
    """ФУНКЦИЯ УДАЛЕНИЯ: Находится здесь, вызывает логику из services"""
    global current_user
    if not current_user: return
    
    print("\n" + "!"*30 + "\nУДАЛЕНИЕ АККАУНТА\n" + "!"*30)
    confirm = input(f"Для подтверждения введите ваше имя ({current_user.name}): ")
    
    if confirm == current_user.name:
        if services.delete_user_completely(session, current_user.id):
            print("Аккаунт успешно удален.")
            current_user = None
        else:
            print("Ошибка при удалении.")
    else:
        print("Имя не совпадает. Отмена.")

# --- ГЛАВНЫЙ ЦИКЛ ---

menu_actions = {
    "1": show_projects, "2": create_project, "3": register_user, 
    "4": login, "5": apply_to_project, "6": show_my_outbox, 
    "7": manage_my_projects_center, "9": delete_my_account
}

while True:
    u_status = current_user.name if current_user else "Гость"
    print(f"\n{'='*40}\n REHUB | {u_status}\n{'='*40}")
    check_new_alerts()
    print("1. Поиск | 2. Создать | 3. Регистрация | 4. Вход")
    print("5. Откликнуться | 6. Мои отклики | 7. Мои проекты")
    print("8. Выход | 9. УДАЛИТЬ АККАУНТ")
    
    choice = input("\nВыбор: ")
    if choice == "8": break
    if action := menu_actions.get(choice): action()