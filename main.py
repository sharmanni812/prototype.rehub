from app import db_session
from app.tables import User, Project  # Импортируем обе таблицы
import os

# 1. Инициализация базы
if not os.path.exists('db'):
    os.makedirs('db')

db_session.global_init("db/projects.db")
session = db_session.create_session()

# 2. Находим тебя (создателя)
me = session.query(User).filter(User.id == 1).first()

if me:
    # 3. Пытаемся создать проект
    project_name = "Rehub Platform"
    existing_project = session.query(Project).filter(Project.title == project_name).first()

    if not existing_project:
        new_project = Project()
        new_project.title = project_name
        new_project.description = "Платформа для поиска единомышленников"
        new_project.leader_id = me.id  # Привязываем к твоему ID

        session.add(new_project)
        session.commit()
        print(f"--- УСПЕХ: Проект '{project_name}' создан! ---")
    else:
        print(f"--- ИНФО: Проект '{project_name}' уже есть в базе ---")

# 4. Финальная проверка: выводим всё, что есть
print("\nВАШИ ПРОЕКТЫ В БАЗЕ:")
projects = session.query(Project).all()
for p in projects:
    # Благодаря orm.relationship мы можем достать имя лидера прямо из объекта проекта
    print(f"ID: {p.id} | Название: {p.title} | Лидер: {me.name}")