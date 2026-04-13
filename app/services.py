from .tables import User, Project, Application

# Константы проекта
ALLOWED_CATEGORIES = ["IT", "Media", "Fashion"]

# --- 1. УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ (USER LOGIC) ---

def create_user(session, name, email, bio="", skills=""):
    """Регистрирует нового пользователя."""
    user = User(name=name, email=email, bio=bio, skills=skills)
    session.add(user)
    session.commit()
    return user

def authenticate_user(session, user_id):
    """Проверяет существование пользователя (для экрана входа в EXE)."""
    try:
        user = session.get(User, int(user_id))
        return user if user else None
    except (ValueError, TypeError):
        return None

def update_user_profile(session, user_id, bio=None, skills=None):
    """Обновляет информацию в профиле (биография, навыки)."""
    user = session.get(User, user_id)
    if user:
        if bio is not None: user.bio = bio
        if skills is not None: user.skills = skills
        session.commit()
        return True
    return False

def get_user_stats(session, user_id):
    """Возвращает цифры для дашборда (личного кабинета)."""
    owned = session.query(Project).filter(Project.leader_id == user_id).count()
    joined = session.query(Application).filter(
        Application.user_id == user_id, 
        Application.status == "Принят"
    ).count()
    pending = session.query(Application).filter(
        Application.user_id == user_id, 
        Application.status == "Ожидание"
    ).count()
    return {"owned": owned, "joined": joined, "pending": pending}

def delete_user_completely(session, user_id):
    """Каскадное удаление пользователя и всех его данных (проектов и заявок)."""
    user = session.get(User, user_id)
    if user:
        session.query(Application).filter(Application.user_id == user_id).delete()
        my_projects = session.query(Project).filter(Project.leader_id == user_id).all()
        for p in my_projects:
            session.query(Application).filter(Application.project_id == p.id).delete()
            session.delete(p)
        session.delete(user)
        session.commit()
        return True
    return False


# --- 2. ЛОГИКА ПРОЕКТОВ (PROJECT LOGIC) ---

def create_project(session, title, description, leader_id, category="IT", roles=""):
    """Создает новый проект с валидацией категории."""
    if category not in ALLOWED_CATEGORIES:
        category = "IT"
    project = Project(
        title=title, description=description, leader_id=leader_id,
        category=category, needed_roles=roles
    )
    session.add(project)
    session.commit()
    return project

def search_projects(session, query):
    """Поиск по ключевому слову (в названии или описании)."""
    search = f"%{query}%"
    return session.query(Project).filter(
        (Project.title.ilike(search)) | (Project.description.ilike(search))
    ).all()

def get_projects_by_category(session, category):
    """Фильтрация проектов по теме."""
    return session.query(Project).filter(Project.category == category).all()

def get_my_projects(session, user_id):
    """Список проектов, где пользователь является лидером."""
    return session.query(Project).filter(Project.leader_id == user_id).all()

def get_projects_i_am_in(session, user_id):
    """Проекты, в которые пользователя приняли как участника."""
    return session.query(Project).join(Application).filter(
        Application.user_id == user_id,
        Application.status == "Принят"
    ).all()

def close_project(session, project_id):
    """Завершает набор в проект."""
    project = session.get(Project, project_id)
    if project:
        project.needed_roles = "КОМАНДА СОБРАНА"
        session.commit()
        return True
    return False

def delete_project(session, project_id):
    """Полное удаление проекта."""
    project = session.get(Project, project_id)
    if project:
        session.query(Application).filter(Application.project_id == project_id).delete()
        session.delete(project)
        session.commit()
        return True
    return False


# --- 3. ЛОГИКА ВЗАИМОДЕЙСТВИЯ (APPLICATION LOGIC) ---

def apply_to_project(session, user_id, project_id, message="Хочу в команду!"):
    """Создает отклик (заявку) на участие."""
    project = session.get(Project, project_id)
    if not project or project.needed_roles == "КОМАНДА СОБРАНА" or project.leader_id == user_id:
        return None
    app = Application(user_id=user_id, project_id=project_id, message=message)
    session.add(app)
    session.commit()
    return app

def update_application_status(session, app_id, new_status):
    """Меняет статус заявки (Принят/Отклонен)."""
    app = session.get(Application, app_id)
    if app:
        app.status = new_status
        session.commit()
        return True
    return False

def get_project_applications(session, project_id):
    """Список всех заявок на проект для лидера."""
    return session.query(Application).filter(Application.project_id == project_id).all()

def get_project_team(session, project_id):
    """Список принятых участников проекта."""
    return session.query(User).join(Application).filter(
        Application.project_id == project_id,
        Application.status == "Принят"
    ).all()