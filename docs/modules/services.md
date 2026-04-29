# ⚙️ Сервисный модуль (services.py)

> **Назначение:** Реализация бизнес-логики ReHub: пользователи, проекты, заявки.
> **Зависимости:** `app.tables`
> **Использование:** импорт функций другими модулями (`from app import services`)

---

## 📋 Оглавление

- [🔧 Константы и импорты](#-константы-и-импорты)
- [👤 Управление пользователями](#-управление-пользователями-user-logic)
- [📁 Логика проектов](#-логика-проектов-project-logic)
- [🔁 Логика взаимодействия](#-логика-взаимодействия-application-logic)

---

## 🔧 Константы и импорты

> ```python
> from app.tables import User, Project, Application
> 
> # Константы проекта
> ALLOWED_CATEGORIES = ["IT", "Media", "Fashion"]
> ```

---

## 👤 Управление пользователями (USER LOGIC)

> ```python
> def create_user(session, name, email, bio="", skills=""):
>     """Регистрирует нового пользователя."""
>     ...
> 
> def authenticate_user(session, user_id):
>     """Проверяет существование пользователя (для экрана входа)."""
>     ...
> 
> def update_user_profile(session, user_id, bio=None, skills=None):
>     """Обновляет информацию в профиле (биография, навыки)."""
>     ...
> 
> def get_user_stats(session, user_id):
>     """Возвращает цифры для дашборда (личного кабинета)."""
>     ...
> 
> def delete_user_completely(session, user_id):
>     """Каскадное удаление пользователя и всех его данных (проектов и заявок)."""
>     ...
> ```

---

## 📁 Логика проектов (PROJECT LOGIC)

> ```python
> def create_project(session, title, description, leader_id, category="IT", roles=""):
>     """Создаёт новый проект с валидацией категории."""
>     ...
> 
> def search_projects(session, query):
>     """Поиск по ключевому слову (в названии или описании)."""
>     ...
> 
> def get_projects_by_category(session, category):
>     """Фильтрация проектов по теме."""
>     ...
> 
> def get_my_projects(session, user_id):
>     """Список проектов, где пользователь является лидером."""
>     ...
> 
> def get_projects_i_am_in(session, user_id):
>     """Проекты, в которые пользователя приняли как участника."""
>     ...
> 
> def close_project(session, project_id):
>     """Завершает набор в проект."""
>     ...
> 
> def delete_project(session, project_id):
>     """Полное удаление проекта."""
>     ...
> ```

---

## 🔁 Логика взаимодействия (APPLICATION LOGIC)

> ```python
> def apply_to_project(session, user_id, project_id, message="Хочу в команду!"):
>     """Создаёт отклик (заявку) на участие."""
>     ...
> 
> def update_application_status(session, app_id, new_status):
>     """Меняет статус заявки (Принят/Отклонен)."""
>     ...
> 
> def get_project_applications(session, project_id):
>     """Список всех заявок на проект для лидера."""
>     ...
> 
> def get_project_team(session, project_id):
>     """Список принятых участников проекта."""
>     ...
> ```