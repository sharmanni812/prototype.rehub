```markdown
# 🖥️ Главный модуль (main.py)

> **Назначение:** Точка входа в консольное приложение ReHub.
> **Зависимости:** `app.db_session`, `app.services`, `app.tables`
> **Запуск:** `python main.py`

---

## 📋 Оглавление

- [🔧 Инициализация приложения](#-инициализация-приложения)
- [📞 Функции-обработчики](#-функции-обработчики-интерфейс-пользователя)
- [🔄 Главный цикл приложения](#-главный-цикл-приложения)

---

## 🔧 Инициализация приложения

> ```python
> from app import db_session, services
> from app.tables import User, Project, Application
> import os
> 
> # 1. Инициализация базы данных
> db_session.global_init("db/projects.db")
> 
> # 2. Создание сессии для работы с БД
> session = db_session.create_session()
> 
> # 3. Определение текущего пользователя
> current_user = session.query(User).first()
> ```

---

## 📞 Функции-обработчики (интерфейс пользователя)

> ```python
> def show_dashboard():
>     """Показывает статистическую сводку на главном экране"""
>     # Выводит: 📊 ВАША СТАТИСТИКА: Лидер в 3 | Участник в 5
> 
> def check_new_alerts():
>     """Проверка уведомлений о статусах заявок"""
>     # Уведомляет: 🔔 +2 принятых / +1 отклоненных
> 
> def show_projects_by_cat():
>     """Пункт меню 1 - фильтрация по категориям (IT, Media, Fashion)"""
> 
> def search_projects():
>     """Пункт меню 2 — глобальный поиск по названию или описанию"""
> 
> def display_project_list(projects, title_text):
>     """Универсальная функция вывода списка проектов [НАБОР]/[ЗАКРЫТ]"""
> 
> def edit_profile():
>     """Пункт меню 4 — редактирование навыков и описания"""
> 
> def create_project():
>     """Пункт меню 3 — создание нового проекта (лидер — current_user)"""
> 
> def register_user():
>     """Пункт меню 5 — регистрация нового аккаунта"""
> 
> def login():
>     """Пункт меню 6 — вход в систему по ID"""
> 
> def apply_to_project():
>     """Пункт меню 7 — подача заявки на участие в проекте"""
> 
> def show_my_outbox():
>     """Пункт меню 8 — просмотр всех исходящих заявок и их статусов"""
> 
> def manage_my_projects_center():
>     """Пункт меню 9 — центр управления заявками и командой"""
> 
> def delete_my_account():
>     """Пункт меню 0 — удаление аккаунта (требует подтверждения имени)"""
> ```

---

## 🔄 Главный цикл приложения

> ```python
> menu_actions = {
>     "1": show_projects_by_cat,
>     "2": search_projects,
>     "3": create_project,
>     "4": edit_profile,
>     "5": register_user,
>     "6": login,
>     "7": apply_to_project,
>     "8": show_my_outbox,
>     "9": manage_my_projects_center,
>     "0": delete_my_account
> }
> 
> while True:
>     # 1. Вызов алертов и дашборда
>     # 2. Отрисовка меню
>     # 3. menu_actions.get(choice)()
> ```