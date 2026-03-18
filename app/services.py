from .tables import User, Project, Application

def apply_to_project(session, user_id, project_id, message="Хочу в команду!"):
    """
    Создает заявку (отклик) от пользователя на участие в проекте.
    Проверяет существование проекта перед созданием.
    """
    project = session.get(Project, project_id)
    if not project:
        return None  # Если проекта нет, заявку создать нельзя
        
    app = Application(user_id=user_id, project_id=project_id, message=message)
    session.add(app)
    session.commit()
    return app

def create_user(session, name, email, bio="", skills=""):
    """
    Регистрирует нового пользователя в системе.
    bio — краткая биография, skills — текстовое описание навыков.
    """
    user = User(name=name, email=email, bio=bio, skills=skills)
    session.add(user)
    session.commit()
    return user

def create_project(session, title, description, leader_id, category="Общее", roles=""):
    """
    Создает новый проект.
    leader_id — ID пользователя, который является автором (лидером).
    needed_roles — строка с перечислением нужных специалистов.
    """
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
    """
    Возвращает список всех существующих проектов из базы данных.
    """
    return session.query(Project).all()

def get_user_notifications(session, user_id):
    """
    Находит все заявки, присланные на проекты конкретного лидера.
    Использует JOIN для связи таблиц заявок и проектов.
    """
    return session.query(Application).join(Project).filter(Project.leader_id == user_id).all()