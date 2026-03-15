import sqlalchemy as sa
from sqlalchemy import orm
from .db_session import SqlAlchemyBase

class User(SqlAlchemyBase):
    __tablename__ = 'users'
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    name = sa.Column(sa.String, nullable=True)
    email = sa.Column(sa.String, index=True, unique=True, nullable=True)
    bio = sa.Column(sa.String, nullable=True)
    skills = sa.Column(sa.String, nullable=True)
    created_date = sa.Column(sa.DateTime, default=sa.func.now())

class Project(SqlAlchemyBase):
    __tablename__ = 'projects'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    title = sa.Column(sa.String, nullable=True)
    description = sa.Column(sa.String, nullable=True)
    
    # СВЯЗЬ: указываем ID пользователя-создателя
    leader_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"))
    
    # Магия: теперь через project.user можно будет получить весь объект создателя
    user = orm.relationship('User')

    def __repr__(self):
        return f'<Project> {self.title}'