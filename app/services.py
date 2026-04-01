from .tables import User, Project, Application

# Константы для проекта — золотой стандарт, чтобы не опечататься в строках
ALLOWED_CATEGORIES = ["IT", "Media", "Fashion"]

def apply_to_project(session, user_id, project_id, message="Хочу в команду!"):
    """
    Создает заявку (отклик) от пользователя на участие в проекте.
    """
    project = session.get(Project, project_id)
    if not project:
        return None
        
    app = Application(user_id=user_id, project_id=project_id, message=message)
    session.add(app)
    session.commit()
    return app

def create_user(session, name, email, bio="", skills=""):
    """Регистрирует нового пользователя."""
    user = User(name=name, email=email, bio=bio, skills=skills)
    session.add(user)
    session.commit()
    return user

def create_project(session, title, description, leader_id, category="IT", roles=""):
    """
    Создает новый проект с валидацией категории.
    Если категория не входит в разрешенные, ставим 'IT' по умолчанию.
    """
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

def get_all_projects(session):
    """Возвращает вообще все проекты."""
    return session.query(Project).all()

def get_projects_by_category(session, category):
    """
    НОВИНКА: Фильтрует проекты по конкретной теме (IT, Media или Fashion).
    """
    return session.query(Project).filter(Project.category == category).all()

def get_user_notifications(session, user_id):
    """Находит уведомления для лидера проектов."""
    return session.query(Application).join(Project).filter(Project.leader_id == user_id).all()
def get_my_projects(session, user_id):
    """Возвращает список проектов, где текущий пользователь — лидер."""
    return session.query(Project).filter(Project.leader_id == user_id).all()

def get_project_applications(session, project_id):
    """Возвращает все заявки на конкретный проект."""
    return session.query(Application).filter(Application.project_id == project_id).all()

def update_application_status(session, app_id, new_status):
    """
    Меняет статус заявки. 
    new_status: 'Принят' или 'Отклонен'.
    """
    app = session.get(Application, app_id)
    if app:
        app.status = new_status
        session.commit()
        return True
    return False

def delete_project(session, project_id):
    """Удаляет проект и все связанные с ним заявки."""
    project = session.get(Project, project_id)
    if project:
        # Сначала удаляем заявки, чтобы не было ошибок связей (Foreign Keys)
        session.query(Application).filter(Application.project_id == project_id).delete()
        session.delete(project)
        session.commit()
        return True
    return False

def get_accepted_applications(session, user_id):
    """Находит все заявки пользователя, которые были одобрены (статус 'Принят')"""
    return session.query(Application).filter(
        Application.user_id == user_id, 
        Application.status == "Принят"
    ).all()