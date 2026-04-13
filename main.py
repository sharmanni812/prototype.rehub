from app import db_session, services
from app.tables import User, Project, Application
import os

# --- ИНИЦИАЛИЗАЦИЯ ---
db_session.global_init("db/projects.db")
session = db_session.create_session()

# Глобальная переменная текущего пользователя (берем первого для теста)
current_user = session.query(User).first()

# --- ФУНКЦИИ-ОБРАБОТЧИКИ (ИНТЕРФЕЙС) ---

def show_dashboard():
    """Показывает краткую сводку активности пользователя"""
    if not current_user: return
    stats = services.get_user_stats(session, current_user.id)
    print(f"\n📊 ВАША СТАТИСТИКА: Лидер в {stats['owned']} | Участник в {stats['joined']} | Ожидание: {stats['pending']}")

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
        print("Подробности в пункте 8.")

def show_projects_by_cat():
    """Просмотр проектов по категориям"""
    print("\n" + "="*20 + "\nНАПРАВЛЕНИЯ:\n1. IT\n2. Media\n3. Fashion\n0. Назад")
    choice = input("\nВыбор темы: ")
    cats = {"1": "IT", "2": "Media", "3": "Fashion"}
    selected = cats.get(choice)
    
    if selected:
        projects = services.get_projects_by_category(session, selected)
        display_project_list(projects, f"КАТЕГОРИЯ: {selected}")

def search_projects():
    """Поиск проектов по ключевому слову"""
    query = input("\n🔍 Введите слово для поиска (название или описание): ")
    results = services.search_projects(session, query)
    display_project_list(results, f"РЕЗУЛЬТАТЫ ПОИСКА ПО '{query}'")

def display_project_list(projects, title_text):
    """Вспомогательная функция для вывода списка проектов"""
    print(f"\n--- {title_text} ---")
    if not projects:
        print("Ничего не найдено.")
    else:
        for p in projects:
            status = "[НАБОР]" if p.needed_roles != "КОМАНДА СОБРАНА" else "[ЗАКРЫТ]"
            print(f"[{p.id}] {status} {p.title}")
        
        pid = input("\nID проекта для деталей (0 - назад): ")
        if pid != "0":
            proj = session.get(Project, pid)
            if proj:
                print(f"\n--- {proj.title} ---\nАвтор: {proj.user.name}\nОписание: {proj.description}")
                print(f"Ищут: {proj.needed_roles}")
                team = services.get_project_team(session, proj.id)
                if team:
                    print(f"В команде: {', '.join([u.name for u in team])}")
                input("\nНажмите Enter...")

def edit_profile():
    """Редактирование профиля текущего пользователя"""
    global current_user
    if not current_user: return print("Войдите в систему!")
    print(f"\n--- РЕДАКТИРОВАНИЕ ПРОФИЛЯ: {current_user.name} ---")
    print(f"Текущие навыки: {current_user.skills or 'Не указаны'}")
    
    new_skills = input("Новые навыки (Enter, чтобы оставить): ")
    new_bio = input("О себе (Enter, чтобы оставить): ")
    
    services.update_user_profile(
        session, current_user.id, 
        bio=new_bio if new_bio else None, 
        skills=new_skills if new_skills else None
    )
    print("Профиль успешно обновлен!")

def create_project():
    if not current_user: return print("Ошибка: Войдите в систему!")
    print("\n--- СОЗДАНИЕ ПРОЕКТА ---")
    t, d = input("Название: "), input("Описание: ")
    c = input("Категория (IT/Media/Fashion): ").strip()
    r = input("Кто нужен (роли): ")
    services.create_project(session, t, d, current_user.id, c, r)
    print("Проект создан!")

def register_user():
    global current_user
    n, e = input("Имя: "), input("Email: ")
    current_user = services.create_user(session, n, e)
    print(f"Аккаунт создан! Ваш ID: {current_user.id}")

def login():
    global current_user
    uid = input("Введите ваш ID: ")
    user = services.authenticate_user(session, uid)
    if user:
        current_user = user
        print(f"Добро пожаловать, {user.name}!")
    else: print("Ошибка: Пользователь не найден.")

def apply_to_project():
    if not current_user: return print("Ошибка: Войдите в систему!")
    pid = input("ID проекта для отклика: ")
    msg = input("Сообщение лидеру: ")
    if services.apply_to_project(session, current_user.id, pid, msg):
        print("Отклик отправлен!")
    else: print("Ошибка: нельзя откликнуться на свой или закрытый проект.")

def show_my_outbox():
    if not current_user: return print("Войдите в систему!")
    apps = session.query(Application).filter(Application.user_id == current_user.id).all()
    print("\n=== МОИ ОТКЛИКИ (ИСХОДЯЩИЕ) ===")
    if not apps: print("Пусто.")
    for a in apps:
        icon = "⏳" if a.status == "Ожидание" else "✅" if a.status == "Принят" else "❌"
        print(f"{icon} Проект: {a.project.title} | Статус: {a.status}")
    input("\nEnter...")

def manage_my_projects_center():
    if not current_user: return print("Войдите в систему!")
    as_leader = services.get_my_projects(session, current_user.id)
    as_member = services.get_projects_i_am_in(session, current_user.id)
    
    print("\n=== ВАШИ ПРОЕКТЫ ===")
    if as_leader:
        print("\n--- Я ЛИДЕР (Управление) ---")
        for p in as_leader: print(f"[{p.id}] {p.title}")
    if as_member:
        print("\n--- Я УЧАСТНИК (Команда) ---")
        for p in as_member: print(f"[{p.id}] {p.title} (Лидер: {p.user.name})")

    pid = input("\nID проекта для управления (0 - назад): ")
    if pid == "0": return
    project = session.get(Project, pid)

    if project and project.leader_id == current_user.id:
        print(f"\n1. Заявки | 2. Команда | 3. Закрыть набор | 4. Удалить проект")
        act = input("Выбор: ")
        if act == "1":
            apps = services.get_project_applications(session, pid)
            for a in apps: print(f"[{a.id}] {a.user.name}: {a.message} ({a.status})")
            aid = input("\nID заявки (0 - назад): ")
            if aid != "0":
                res = input("1. Принять | 2. Отклонить: ")
                services.update_application_status(session, aid, "Принят" if res == "1" else "Отклонен")
        elif act == "2":
            team = services.get_project_team(session, pid)
            for m in team: print(f"- {m.name} ({m.email})")
            input("\nEnter...")
        elif act == "3": services.close_project(session, pid)
        elif act == "4": services.delete_project(session, pid)
    elif project:
        print(f"\nПроект: {project.title}. Вы участник команды.")
        input("Enter...")

def delete_my_account():
    global current_user
    if not current_user: return
    print("\n" + "!"*30 + "\nУДАЛЕНИЕ АККАУНТА\n" + "!"*30)
    confirm = input(f"Введите ваше имя ({current_user.name}) для подтверждения: ")
    if confirm == current_user.name:
        if services.delete_user_completely(session, current_user.id):
            print("Аккаунт удален. Прощайте!")
            current_user = None
    else: print("Отмена удаления.")

# --- ГЛАВНЫЙ ЦИКЛ ---

menu_actions = {
    "1": show_projects_by_cat,
    "2": search_projects,
    "3": create_project,
    "4": edit_profile,
    "5": register_user,
    "6": login,
    "7": apply_to_project,
    "8": show_my_outbox,
    "9": manage_my_projects_center,
    "0": delete_my_account
}

while True:
    u_status = current_user.name if current_user else "Гость"
    print(f"\n{'='*45}\n REHUB SYSTEM | Пользователь: {u_status}\n{'='*45}")
    
    check_new_alerts()
    show_dashboard()
    
    print("\n1. Поиск по категориям")
    print("2. ГЛОБАЛЬНЫЙ ПОИСК")
    print("3. Создать проект")
    print("4. РЕДАКТИРОВАТЬ ПРОФИЛЬ")
    print("5. Регистрация | 6. Вход")
    print("7. Откликнуться на проект")
    print("8. Статусы моих откликов")
    print("9. МОИ ПРОЕКТЫ (Входящие/Команды)")
    print("0. УДАЛИТЬ АККАУНТ")
    print("exit - Выход")
    
    choice = input("\nВаш выбор: ")
    if choice == "exit": break
    if action := menu_actions.get(choice): action()
    else: print("Неверный ввод.")