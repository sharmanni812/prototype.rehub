import sqlalchemy as sa
from .db_session import SqlAlchemyBase

class User(SqlAlchemyBase):
    """
    Модель пользователя.
    Хранит личные данные, био и профессиональные навыки.
    """
    __tablename__ = 'users'
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    name = sa.Column(sa.String, nullable=False)
    email = sa.Column(sa.String, unique=True, nullable=False) # Уникальный адрес для входа
    bio = sa.Column(sa.String, nullable=True)
    # Навыки (хранятся в виде текста, например: "Python, SQL, UI/UX")
    skills = sa.Column(sa.String, nullable=True) 

class Project(SqlAlchemyBase):
    """
    Модель проекта.
    Связана с пользователем (лидером) через leader_id.
    """
    __tablename__ = 'projects'
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    title = sa.Column(sa.String, nullable=False)
    description = sa.Column(sa.String, nullable=True)
    
    # Внешний ключ: указывает на id в таблице users
    leader_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"))
    
    category = sa.Column(sa.String, default="Общее")
    needed_roles = sa.Column(sa.String, nullable=True) # Кого ищут: "Дизайнер, Frontend"

    # ORM-связь: позволяет писать project.user.name, чтобы получить имя лидера
    user = sa.orm.relationship('User')

class Application(SqlAlchemyBase):
    """
    Модель заявки на участие.
    Связующее звено между пользователем, который хочет вступить, и проектом.
    """
    __tablename__ = 'applications'
    
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    # Ссылка на проект, в который подается заявка
    project_id = sa.Column(sa.Integer, sa.ForeignKey("projects.id"))
    # Ссылка на пользователя, который подает заявку
    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"))
    
    message = sa.Column(sa.String, nullable=True) # Сопроводительное письмо
    status = sa.Column(sa.String, default="Ожидание") # Возможные: Ожидание, Принят, Отклонен

    # Удобные ссылки для кода (доступ к объектам через точку)
    project = sa.orm.relationship('Project')
    user = sa.orm.relationship('User')