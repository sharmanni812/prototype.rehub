from app import db_session, services
from app.tables import User
import os

db_session.global_init("db/projects.db")
session = db_session.create_session()

# Для тестов берем тебя как лидера (ID 1)
current_user = session.query(User).get(1)

while True:
    print("\n--- REHUB CLI ---")
    print("1. Список проектов")
    print("2. Создать проект")
    print("3. Выход")
    
    choice = input("Выберите действие: ")
    
    if choice == "1":
        projects = services.get_all_projects(session)
        for p in projects:
            print(f"[{p.id}] {p.title} | Автор: {p.user.name}")
            
    elif choice == "2":
        t = input("Название: ")
        d = input("Описание: ")
        services.create_project(session, t, d, current_user.id)
        print("Проект добавлен!")
        
    elif choice == "3":
        break