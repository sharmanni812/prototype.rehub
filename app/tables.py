import sqlalchemy as sa
from .db_session import SqlAlchemyBase

class User(SqlAlchemyBase):
    __tablename__ = 'users'

    # Уникальный номер пользователя (создается автоматически)
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    
    # Основная информация
    name = sa.Column(sa.String, nullable=True)
    email = sa.Column(sa.String, index=True, unique=True, nullable=True)
    
    # Профессиональные данные
    bio = sa.Column(sa.String, nullable=True)
    skills = sa.Column(sa.String, nullable=True)
    
    # Системное поле: когда пользователь был создан
    created_date = sa.Column(sa.DateTime, default=sa.func.now())

    def __repr__(self):
        return f'<User> {self.id} {self.name} {self.email}'