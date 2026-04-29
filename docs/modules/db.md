```markdown
# 🗄️ Модуль базы данных (db_session.py + tables.py)

> **Назначение:** Инициализация и управление базой данных SQLite, ORM-модели таблиц.
> **Зависимости:** `sqlalchemy`
> **Файлы:** `app/db_session.py`, `app/tables.py`

---

## 📋 Оглавление

- [🔧 Инициализация базы данных](#-инициализация-базы-данных-db_sessionpy)
- [👤 Модель User](#-модель-user-users)
- [📁 Модель Project](#-модель-project-projects)
- [🔁 Модель Application](#-модель-application-applications)

---

## 🔧 Инициализация базы данных (db_session.py)

> ```python
> import sqlalchemy as sa
> import sqlalchemy.orm as orm
> from sqlalchemy.orm import Session
> import sqlalchemy.ext.declarative as dec
> 
> # служебный объект. хранение структур таблиц из tables.py
> SqlAlchemyBase = dec.declarative_base()
> 
> # внутренняя переменная. хранение настроенного объекта для создания сессий
> __factory = None
> 
> def global_init(db_file): 
>     # физическое создание базы данных и настройка связи
>     global __factory
> 
>     if __factory:
>         return
> 
>     if not db_file or not db_file.strip():
>         raise Exception("Укажите файл базы данных!")
>     
>     # формирование пути к файлу базы данных
>     conn_str = f'sqlite:///{db_file.strip()}?check_same_thread=False'
>     
>     # движок. перевод команд python в команды файловой системы
>     engine = sa.create_engine(conn_str, echo=False)
>     
>     # генератор сессий. привязывание этого генератора к конкретному движку.
>     __factory = orm.sessionmaker(bind=engine)
> 
>     from . import tables
>     
>     # команда на выполнение. создание таблиц в файле на диске
>     SqlAlchemyBase.metadata.create_all(engine)
> 
> def create_session() -> Session:
>     # создание нового окна связи (сессии) для работы с данными
>     global __factory
>     return __factory()
> ```

---

## 👤 Модель User (users)

> ```python
> import sqlalchemy as sa
> from .db_session import SqlAlchemyBase
> 
> class User(SqlAlchemyBase):
>     """
>     Модель пользователя.
>     Хранит личные данные, био и профессиональные навыки.
>     """
>     __tablename__ = 'users'
>     id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
>     name = sa.Column(sa.String, nullable=False)
>     email = sa.Column(sa.String, unique=True, nullable=False)
>     bio = sa.Column(sa.String, nullable=True)
>     skills = sa.Column(sa.String, nullable=True)
> ```

---

## 📁 Модель Project (projects)

> ```python
> class Project(SqlAlchemyBase):
>     """
>     Модель проекта.
>     Связана с пользователем (лидером) через leader_id.
>     """
>     __tablename__ = 'projects'
>     id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
>     title = sa.Column(sa.String, nullable=False)
>     description = sa.Column(sa.String, nullable=True)
>     
>     # Внешний ключ: указывает на id в таблице users
>     leader_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"))
>     
>     category = sa.Column(sa.String, default="Общее")
>     needed_roles = sa.Column(sa.String, nullable=True)
> 
>     # ORM-связь: позволяет писать project.user.name, чтобы получить имя лидера
>     user = sa.orm.relationship('User')
> ```

---

## 🔁 Модель Application (applications)

> ```python
> class Application(SqlAlchemyBase):
>     """
>     Модель заявки на участие.
>     Связующее звено между пользователем, который хочет вступить, и проектом.
>     """
>     __tablename__ = 'applications'
>     
>     id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
>     # Ссылка на проект, в который подается заявка
>     project_id = sa.Column(sa.Integer, sa.ForeignKey("projects.id"))
>     # Ссылка на пользователя, который подает заявку
>     user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"))
>     
>     message = sa.Column(sa.String, nullable=True)
>     status = sa.Column(sa.String, default="Ожидание")
> 
>     # Удобные ссылки для кода (доступ к объектам через точку)
>     project = sa.orm.relationship('Project')
>     user = sa.orm.relationship('User')
> ```