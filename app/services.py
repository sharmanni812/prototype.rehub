from .tables import User, Project, Application

# Константы для проекта
ALLOWED_CATEGORIES = ["IT", "Media", "Fashion"]

# --- РАБОТА С ПОЛЬЗОВАТЕЛЯМИ ---

def create_user(session, name, email, bio="", skills=""):
    """Регистрирует нового пользователя."""
    user = User(name=name, email=email, bio=bio, skills=skills)
    session.add(user)
    session.commit()
    return user

def delete_user_completely(session, user_id):
    """
    Полное удаление пользователя и всех его следов.
    Удаляет отклики пользователя и его собственные проекты (вместе с чужими откликами в них).
    """
    user = session.get(User, user_id)
    if user:
        # 1. Удаляем все отклики самого пользователя в чужие проекты
        session.query(Application).filter(Application.user_id == user_id).delete()
        
        # 2. Находим проекты, где он лидер
        my_projects = session.query(Project).filter(Project.leader_id == user_id).all()
        for p in my_projects:
            # Удаляем все отклики других людей в эти проекты
            session.query(Application).filter(Application.project_id == p.id).delete()
            session.delete(p)
        
        # 3. Удаляем самого пользователя
        session.delete(user)
        session.commit()
        return True
    return False


# --- РАБОТА С ПРОЕКТАМИ ---

def create_project(session, title, description, leader_id, category="IT", roles=""):
    """Создает новый проект с валидацией категории."""
    if category not in ALLOWED_CATEGORIES:
        category = "IT"

    project = Project(
        title=title, 
        description=description, 
        leader_id=leader_id,
        category=category,
        needed_roles=roles
    )
    session.add(project)
    session.commit()
    return project

def get_projects_by_category(session, category):
    """Фильтрует проекты по конкретной теме."""
    return session.query(Project).filter(Project.category == category).all()

def get_my_projects(session, user_id):
    """Возвращает список проектов, где пользователь — лидер."""
    return session.query(Project).filter(Project.leader_id == user_id).all()

def get_projects_i_am_in(session, user_id):
    """Находит проекты, в которые пользователя ПРИНЯЛИ как участника."""
    return session.query(Project).join(Application).filter(
        Application.user_id == user_id,
        Application.status == "Принят"
    ).all()

def delete_project(session, project_id):
    """Удаляет проект и все связанные с ним заявки."""
    project = session.get(Project, project_id)
    if project:
        session.query(Application).filter(Application.project_id == project_id).delete()
        session.delete(project)
        session.commit()
        return True
    return False

def close_project(session, project_id):
    """Помечает проект как укомплектованный."""
    project = session.get(Project, project_id)
    if project:
        project.needed_roles = "КОМАНДА СОБРАНА"
        session.commit()
        return True
    return False


# --- РАБОТА С ЗАЯВКАМИ (ОТКЛИКАМИ) ---

def apply_to_project(session, user_id, project_id, message="Хочу в команду!"):
    """Создает отклик на проект."""
    project = session.get(Project, project_id)
    # Нельзя откликнуться, если проекта нет или набор закрыт
    if not project or project.needed_roles == "КОМАНДА СОБРАНА":
        return None
    
    # Нельзя откликнуться на свой же проект
    if project.leader_id == user_id:
        return None
        
    app = Application(user_id=user_id, project_id=project_id, message=message)
    session.add(app)
    session.commit()
    return app

def get_project_applications(session, project_id):
    """Возвращает все заявки на конкретный проект для лидера."""
    return session.query(Application).filter(Application.project_id == project_id).all()

def update_application_status(session, app_id, new_status):
    """Меняет статус заявки ('Принят'/'Отклонен')."""
    app = session.get(Application, app_id)
    if app:
        app.status = new_status
        session.commit()
        return True
    return False

def get_project_team(session, project_id):
    """Возвращает список участников (User), которые были ПРИНЯТЫ в проект."""
    return session.query(User).join(Application).filter(
        Application.project_id == project_id,
        Application.status == "Принят"
    ).all()