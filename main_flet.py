import flet as ft
from app import db_session, services
from app.tables import User, Project, Application


class RehubApp:
    """Главный класс приложения REHUB"""

    def __init__(self):
        self.session = None
        self.current_user = None
        self.theme_mode = ft.ThemeMode.DARK
        self.page = None
        self.theme_button = None
        self.suggestions_column = None
        self.fixed_height_container = None
        self.current_category = "Все"
        self.current_search_query = ""

    # Инициализация базы данных
    def init_db(self):
        db_session.global_init("db/projects.db")
        self.session = db_session.create_session()

    # Настройка страницы
    def setup_page(self, page: ft.Page):
        self.page = page
        page.title = "REHUB"
        page.theme_mode = self.theme_mode
        page.window_width = 1000
        page.window_height = 750
        page.padding = 20
        page.scroll = ft.ScrollMode.AUTO

    # Создание кнопки темы
    def _create_theme_button(self):
        self.theme_button = ft.IconButton(
            icon=ft.Icons.DARK_MODE,
            icon_size=30,
            on_click=self.toggle_theme,
            tooltip="Сменить тему",
        )

    # Переключение темы
    def toggle_theme(self, e):
        if self.theme_mode == ft.ThemeMode.DARK:
            self.theme_mode = ft.ThemeMode.LIGHT
            self.page.theme_mode = ft.ThemeMode.LIGHT
            self.theme_button.icon = ft.Icons.LIGHT_MODE
        else:
            self.theme_mode = ft.ThemeMode.DARK
            self.page.theme_mode = ft.ThemeMode.DARK
            self.theme_button.icon = ft.Icons.DARK_MODE
        self.page.update()

    # Очистка страницы и добавление контента
    def clear_and_add(self, content):
        self.page.clean()
        self.page.add(content)
        self.page.update()

    def clear(self):
        self.page.controls.clear()
        self.page.update()

    # Сравнение имён с первой буквой без учёта регистра
    def names_equal(self, name1, name2):
        if len(name1) != len(name2):
            return False
        if name1[0].lower() != name2[0].lower():
            return False
        return name1[1:] == name2[1:]

    # Поиск по началу слов
    def matches_search(self, text, query):
        if not query:
            return True
        query_lower = query.lower()
        words = text.lower().split()
        for word in words:
            if word.startswith(query_lower):
                return True
        return False

    # Проверка уникальности имени
    def is_name_unique(self, name, exclude_user_id=None):
        all_users = self.session.query(User).all()
        for user in all_users:
            if exclude_user_id and user.id == exclude_user_id:
                continue
            if self.names_equal(user.name, name):
                return False
        return True

    # Умный вход
    def smart_login(self, login_input):
        value = login_input.strip()
        if value.isdigit():
            user = services.authenticate_user(self.session, value)
            if user:
                return user
        user = self.session.query(User).filter(User.email == value).first()
        if user:
            return user
        all_users = self.session.query(User).all()
        for user in all_users:
            if self.names_equal(user.name, value):
                return user
        return None

    # Обновление профиля
    def update_user_profile(self, user_id, name=None, email=None, bio=None, skills=None):
        errors = []

        if name is not None:
            if len(name.strip()) < 2:
                errors.append("Имя должно содержать хотя бы 2 символа")
            else:
                if not self.is_name_unique(name, user_id):
                    errors.append("Это имя уже занято")

        if email is not None:
            if "@" not in email or "." not in email:
                errors.append("Введите корректный email")
            else:
                existing = self.session.query(User).filter(User.email == email).first()
                if existing and existing.id != user_id:
                    errors.append("Этот email уже зарегистрирован")

        if errors:
            return False, errors

        user = self.session.get(User, user_id)
        if user:
            if name is not None:
                user.name = name
            if email is not None:
                user.email = email
            if bio is not None:
                user.bio = bio
            if skills is not None:
                user.skills = skills
            self.session.commit()
            return True, []
        return False, ["Пользователь не найден"]

    # ========== ЭКРАН ВХОДА ==========
    def show_login(self):
        self.clear()
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        login_field = ft.TextField(
            label="Email, ID или имя пользователя",
            width=400,
            autofocus=True,
            hint_text="Введите email, ID или имя"
        )
        error_text = ft.Text("", color=ft.Colors.RED)

        def do_login(e):
            user = self.smart_login(login_field.value)
            if user:
                self.current_user = user
                self.show_dashboard()
            else:
                error_text.value = "Пользователь не найден"
                self.page.update()

        login_field.on_submit = do_login
        self._create_theme_button()

        content = ft.Column([
            ft.Row([ft.Container(expand=True), self.theme_button]),
            ft.Container(expand=True),
            ft.Column([
                ft.Text("REHUB", size=48, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_400),
                ft.Text("Вход в систему", size=20),
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                login_field,
                ft.FilledButton("Войти", on_click=do_login, width=400),
                ft.TextButton("Нет аккаунта? Зарегистрироваться", on_click=lambda _: self.show_register()),
                error_text,
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
            ft.Container(expand=True),
        ], expand=True)

        self.clear_and_add(content)

    # ========== ЭКРАН РЕГИСТРАЦИИ ==========
    def show_register(self):
        self.clear()
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        name_field = ft.TextField(label="Имя", width=400)
        email_field = ft.TextField(label="Email", width=400)
        reg_error = ft.Text("", color=ft.Colors.RED)
        reg_success = ft.Text("", color=ft.Colors.GREEN)

        def do_register(e):
            reg_error.value = ""
            reg_success.value = ""
            self.page.update()

            if not name_field.value or not name_field.value.strip():
                reg_error.value = "Введите имя"
                self.page.update()
                return

            if not email_field.value or not email_field.value.strip():
                reg_error.value = "Введите email"
                self.page.update()
                return

            name = name_field.value.strip()
            email = email_field.value.strip()

            if len(name) < 2:
                reg_error.value = "Имя должно содержать хотя бы 2 символа"
                self.page.update()
                return

            if "@" not in email or "." not in email:
                reg_error.value = "Введите корректный email"
                self.page.update()
                return

            existing_name = self.session.query(User).filter(User.name == name).first()
            if existing_name:
                reg_error.value = f"Имя '{name}' уже занято"
                self.page.update()
                return

            existing_email = self.session.query(User).filter(User.email == email).first()
            if existing_email:
                reg_error.value = f"Email '{email}' уже зарегистрирован"
                self.page.update()
                return

            try:
                user = services.create_user(self.session, name, email, "", "")
                self.current_user = user
                reg_success.value = f"Регистрация успешна! Добро пожаловать, {name}!"
                self.page.update()

                import threading
                threading.Timer(1.5, lambda: self.show_dashboard()).start()

            except Exception as ex:
                reg_error.value = f"Ошибка регистрации: {ex}"
                self.page.update()

        self._create_theme_button()

        content = ft.Column([
            ft.Row([ft.IconButton(ft.Icons.HOME, on_click=lambda _: self.show_login()), ft.Container(expand=True), self.theme_button]),
            ft.Container(expand=True),
            ft.Column([
                ft.Text("Регистрация", size=32, weight=ft.FontWeight.BOLD),
                ft.Text("Нужны только имя и email", size=12, color=ft.Colors.GREY_500),
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                name_field,
                email_field,
                ft.FilledButton("Зарегистрироваться", on_click=do_register, width=400),
                reg_error,
                reg_success,
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
            ft.Container(expand=True),
        ], expand=True)

        self.clear_and_add(content)

    # ========== ДАШБОРД ==========
    def show_dashboard(self):
        self.clear()
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        if self.current_user is None:
            self.show_login()
            return

        self._create_theme_button()

        stats = services.get_user_stats(self.session, self.current_user.id)

        incoming_apps = self.session.query(Application).join(Project).filter(
            Project.leader_id == self.current_user.id,
            Application.status == "Ожидание"
        ).all()

        accepted_apps = self.session.query(Application).filter(
            Application.user_id == self.current_user.id,
            Application.status == "Принят"
        ).all()

        logout_button = ft.IconButton(
            icon=ft.Icons.LOGOUT,
            icon_size=24,
            on_click=lambda _: self.show_login(),
            tooltip="Выйти из аккаунта",
        )

        top_bar = ft.Row([
            ft.Container(expand=True),
            logout_button,
            self.theme_button,
        ])

        nav_menu = ft.Column([
            ft.TextButton("Профиль", icon=ft.Icons.PERSON, on_click=lambda _: self.show_settings(), width=200),
            ft.TextButton("Найти проект", icon=ft.Icons.SEARCH, on_click=lambda _: self.show_find_projects(), width=200),
            ft.TextButton("Мои проекты", icon=ft.Icons.FOLDER, on_click=lambda _: self.show_my_projects_list(), width=200),
            ft.TextButton("Заявки", icon=ft.Icons.LIST_ALT, on_click=lambda _: self.show_applications_list(), width=200),
            ft.TextButton("Пользователи", icon=ft.Icons.PEOPLE, on_click=lambda _: self.show_users_list(), width=200),
        ], spacing=10, alignment=ft.MainAxisAlignment.START)

        notifications = []

        if len(incoming_apps) > 0:
            notifications.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.NOTIFICATIONS, color=ft.Colors.ORANGE),
                        ft.Text(f"У вас {len(incoming_apps)} новых входящих заявок!", color=ft.Colors.ORANGE),
                        ft.TextButton("Перейти", on_click=lambda _: self.show_applications_list()),
                    ]),
                    padding=10,
                    bgcolor=ft.Colors.ORANGE_900 if self.theme_mode == ft.ThemeMode.DARK else ft.Colors.ORANGE_100,
                    border_radius=10,
                )
            )

        if len(accepted_apps) > 0:
            notifications.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN),
                        ft.Text(f"Ваша заявка принята в {len(accepted_apps)} проект(ах)!", color=ft.Colors.GREEN),
                        ft.TextButton("Перейти", on_click=lambda _: self.show_applications_list()),
                    ]),
                    padding=10,
                    bgcolor=ft.Colors.GREEN_900 if self.theme_mode == ft.ThemeMode.DARK else ft.Colors.GREEN_100,
                    border_radius=10,
                )
            )

        if stats['pending'] > 0:
            notifications.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.HOURGLASS_EMPTY, color=ft.Colors.YELLOW),
                        ft.Text(f"Ожидают ответа по {stats['pending']} заявкам", color=ft.Colors.YELLOW),
                    ]),
                    padding=10,
                    bgcolor=ft.Colors.YELLOW_900 if self.theme_mode == ft.ThemeMode.DARK else ft.Colors.YELLOW_100,
                    border_radius=10,
                )
            )

        search_functions = ft.TextField(
            hint_text="Поиск...",
            width=300,
            on_change=self.search_functions
        )

        right_panel_top = ft.Column([
            ft.Text(f"Приветствие, {self.current_user.name}!", size=24, weight=ft.FontWeight.BOLD),
            ft.Text(f"ID: {self.current_user.id}", size=14, color=ft.Colors.GREY_400),
            ft.Divider(height=10),
            ft.Column(notifications, spacing=10) if notifications else ft.Text("Нет новых уведомлений", color=ft.Colors.GREY_500),
            ft.Divider(height=10),
            search_functions,
        ], spacing=15)

        stats_container = ft.Container(
            content=ft.Column([
                ft.Text("Моя статистика", size=16, weight=ft.FontWeight.BOLD),
                ft.Text(f"Веду проектов: {stats['owned']}", size=14),
                ft.Text(f"Участвую: {stats['joined']}", size=14),
                ft.Text(f"Ожидают ответа: {stats['pending']}", size=14),
            ], spacing=5),
            padding=15,
            bgcolor=ft.Colors.BLUE_GREY_900 if self.theme_mode == ft.ThemeMode.DARK else ft.Colors.GREY_200,
            border_radius=10,
        )

        top_row = ft.Row([
            right_panel_top,
            stats_container,
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, spacing=20)

        self.suggestions_column = ft.Column(spacing=5)
        self.fixed_height_container = ft.Container(
            content=self.suggestions_column,
            height=150,
            visible=True
        )

        right_panel_full = ft.Column([
            top_row,
            self.fixed_height_container,
        ], spacing=10)

        content = ft.Row([
            ft.Container(nav_menu, width=200),
            ft.VerticalDivider(width=1),
            ft.Container(right_panel_full, expand=True, padding=20),
        ], expand=True)

        self.clear_and_add(ft.Column([top_bar, content], expand=True))

    # ========== БЫСТРЫЙ ПОИСК ПО ФУНКЦИЯМ ==========
    def search_functions(self, e):
        query = e.control.value.lower()
        self.suggestions_column.controls.clear()

        functions = {
            "профиль": self.show_settings,
            "настройки": self.show_settings,
            "найти проект": self.show_find_projects,
            "поиск": self.show_find_projects,
            "мои проекты": self.show_my_projects_list,
            "заявки": self.show_applications_list,
            "отклики": self.show_applications_list,
            "пользователи": self.show_users_list,
            "участники": self.show_users_list,
        }

        suggestions = []
        if query:
            for key, func in functions.items():
                if self.matches_search(key, query):
                    suggestions.append(ft.TextButton(key, on_click=lambda e, f=func: self.navigate_to(f)))

        if suggestions:
            for s in suggestions:
                self.suggestions_column.controls.append(s)
        else:
            self.suggestions_column.controls.append(ft.Text("Ничего не найдено", color=ft.Colors.GREY_500))

        self.page.update()

    def navigate_to(self, func):
        func()
        self.suggestions_column.controls.clear()
        self.page.update()

    # ========== ЭКРАН НАСТРОЕК (ПРОФИЛЬ) ==========
    def show_settings(self):
        self.clear()
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        name_field = ft.TextField(label="Имя", value=self.current_user.name, width=400)
        email_field = ft.TextField(label="Email", value=self.current_user.email, width=400)
        skills_field = ft.TextField(label="Навыки", value=self.current_user.skills or "", width=400)
        bio_field = ft.TextField(label="О себе", value=self.current_user.bio or "", multiline=True, height=80, width=400)

        save_status = ft.Text("", color=ft.Colors.GREEN)
        error_status = ft.Text("", color=ft.Colors.RED)

        def save_profile(e):
            success, errors = self.update_user_profile(
                self.current_user.id,
                name=name_field.value.strip(),
                email=email_field.value.strip(),
                bio=bio_field.value,
                skills=skills_field.value
            )
            if success:
                self.current_user = self.session.get(User, self.current_user.id)
                save_status.value = "Профиль сохранён"
                error_status.value = ""
                self.page.update()
                import threading
                threading.Timer(2, lambda: setattr(save_status, "value", "") or self.page.update()).start()
            else:
                error_status.value = "\n".join(errors)
                save_status.value = ""
                self.page.update()

        def delete_account(e):
            def confirm_delete(e):
                try:
                    user = self.session.get(User, self.current_user.id)
                    if user:
                        self.session.query(Application).filter(Application.user_id == user.id).delete()
                        my_projects = self.session.query(Project).filter(Project.leader_id == user.id).all()
                        for p in my_projects:
                            self.session.query(Application).filter(Application.project_id == p.id).delete()
                            self.session.delete(p)
                        self.session.delete(user)
                        self.session.commit()

                        self.page.snack_bar = ft.SnackBar(content=ft.Text("Аккаунт удалён"), bgcolor=ft.Colors.GREEN)
                        self.page.snack_bar.open = True
                        self.page.update()

                        self.current_user = None
                        self.show_login()
                except Exception as ex:
                    self.page.snack_bar = ft.SnackBar(content=ft.Text(f"Ошибка: {ex}"), bgcolor=ft.Colors.RED)
                    self.page.snack_bar.open = True
                    self.page.update()

            dialog = ft.AlertDialog(
                title=ft.Text("Удаление аккаунта"),
                content=ft.Text("Вы уверены? Все данные будут удалены безвозвратно."),
                actions=[
                    ft.TextButton("Отмена", on_click=lambda e: setattr(dialog, "open", False)),
                    ft.FilledButton("Удалить", on_click=confirm_delete, bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE),
                ]
            )
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()

        self._create_theme_button()

        content = ft.Column([
            ft.Row([ft.IconButton(ft.Icons.HOME, on_click=lambda _: self.show_dashboard()), ft.Container(expand=True), self.theme_button]),
            ft.Container(expand=True),
            ft.Column([
                ft.Text("Настройки", size=32, weight=ft.FontWeight.BOLD),
                name_field,
                email_field,
                skills_field,
                bio_field,
                ft.Row([
                    ft.FilledButton("Сохранить", on_click=save_profile, width=150),
                    ft.OutlinedButton("Отмена", on_click=lambda _: self.show_dashboard(), width=150),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
                save_status,
                error_status,
                ft.Divider(height=20),
                ft.FilledButton(
                    "Удалить аккаунт",
                    on_click=delete_account,
                    width=250,
                    bgcolor=ft.Colors.RED_700,
                    color=ft.Colors.WHITE
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
            ft.Container(expand=True),
        ], expand=True)

        self.clear_and_add(content)

    # ========== ЭКРАН ПОИСКА ПРОЕКТОВ ==========
    def show_find_projects(self):
        self.clear()
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        search_field = ft.TextField(
            label="Поиск проектов",
            hint_text="Введите название",
            width=400,
        )
        category_filter = ft.Dropdown(
            label="Категория",
            options=[
                ft.dropdown.Option("Все"),
                ft.dropdown.Option("IT"),
                ft.dropdown.Option("Media"),
                ft.dropdown.Option("Fashion"),
            ],
            value="Все",
            width=200,
        )
        projects_list = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
        search_result_text = ft.Text("", size=14, color=ft.Colors.GREY_500)

        all_projects = self.session.query(Project).all()
        user_applications = {app.project_id for app in self.session.query(Application).filter(Application.user_id == self.current_user.id).all()}

        def load_projects():
            projects_list.controls.clear()

            if category_filter.value == "Все":
                filtered = all_projects.copy()
            else:
                filtered = [p for p in all_projects if p.category == category_filter.value]

            query = search_field.value.lower() if search_field.value else ""
            if query:
                filtered = [p for p in filtered if query in p.title.lower() or (p.description and query in p.description.lower())]

            filtered = [p for p in filtered if p.leader_id != self.current_user.id]

            if not filtered:
                search_result_text.value = "Проектов не найдено"
            else:
                search_result_text.value = f"Найдено: {len(filtered)}"
                for p in filtered:
                    already_applied = p.id in user_applications
                    button_text = "Заявка отправлена" if already_applied else "Подробнее"
                    button_disabled = already_applied

                    projects_list.controls.append(
                        ft.Card(
                            content=ft.Container(
                                content=ft.Column([
                                    ft.Text(p.title, size=18, weight=ft.FontWeight.BOLD),
                                    ft.Text(p.description[:100] + "..." if p.description else "", size=14, color=ft.Colors.GREY_400),
                                    ft.Text(f"Категория: {p.category} | Лидер: {p.user.name if p.user else 'Неизвестный'}", size=12, color=ft.Colors.BLUE_400),
                                    ft.FilledButton(button_text, width=150, disabled=button_disabled, on_click=lambda e, proj=p: self.show_project_detail_page(proj) if not button_disabled else None),
                                ], spacing=8),
                                padding=15,
                            )
                        )
                    )
            self.page.update()

        category_filter.on_change = lambda e: load_projects()
        search_field.on_change = lambda e: load_projects()
        search_field.on_submit = lambda e: load_projects()

        self._create_theme_button()

        self.page.clean()
        self.page.add(
            ft.Column([
                ft.Row([ft.IconButton(ft.Icons.HOME, on_click=lambda _: self.show_dashboard()), ft.Container(expand=True), self.theme_button]),
                ft.Column([
                    ft.Text("Поиск проектов", size=32, weight=ft.FontWeight.BOLD),
                    ft.Row([search_field, category_filter], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
                    search_result_text,
                    projects_list,
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15, expand=True),
            ], expand=True)
        )
        self.page.update()
        load_projects()

    # ========== ЭКРАН ДЕТАЛЕЙ ПРОЕКТА ==========
    def show_project_detail_page(self, project):
        already_applied = self.session.query(Application).filter(
            Application.user_id == self.current_user.id,
            Application.project_id == project.id,
            Application.status == "Ожидание"
        ).first() is not None

        is_own_project = project.leader_id == self.current_user.id

        def apply_to_project(e):
            result = services.apply_to_project(self.session, self.current_user.id, project.id, "Хочу в команду!")
            if result:
                self.page.snack_bar = ft.SnackBar(content=ft.Text("Заявка отправлена!"), bgcolor=ft.Colors.GREEN)
                self.page.snack_bar.open = True
                self.show_find_projects()
            else:
                self.page.snack_bar = ft.SnackBar(content=ft.Text("Не удалось откликнуться"), bgcolor=ft.Colors.RED)
                self.page.snack_bar.open = True
            self.page.update()

        def cancel_application(e):
            app = self.session.query(Application).filter(
                Application.user_id == self.current_user.id,
                Application.project_id == project.id,
                Application.status == "Ожидание"
            ).first()
            if app:
                self.session.delete(app)
                self.session.commit()
                self.page.snack_bar = ft.SnackBar(content=ft.Text("Заявка отменена"), bgcolor=ft.Colors.GREEN)
                self.page.snack_bar.open = True
                self.show_find_projects()
            self.page.update()

        def close_project(e):
            services.close_project(self.session, project.id)
            self.page.snack_bar = ft.SnackBar(content=ft.Text("Набор в проект закрыт"), bgcolor=ft.Colors.GREEN)
            self.page.snack_bar.open = True
            self.show_my_projects_list()
            self.page.update()

        def delete_project(e):
            def confirm_delete(e):
                services.delete_project(self.session, project.id)
                self.page.snack_bar = ft.SnackBar(content=ft.Text("Проект удалён"), bgcolor=ft.Colors.GREEN)
                self.page.snack_bar.open = True
                self.show_my_projects_list()
                self.page.update()

            dialog = ft.AlertDialog(
                title=ft.Text("Удаление проекта"),
                content=ft.Text("Вы уверены? Проект будет удалён безвозвратно."),
                actions=[
                    ft.TextButton("Отмена", on_click=lambda e: setattr(dialog, "open", False)),
                    ft.FilledButton("Удалить", on_click=confirm_delete, bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE),
                ]
            )
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()

        def go_back(e):
            self.show_find_projects()

        self.clear()
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        action_buttons = []
        if is_own_project:
            if project.needed_roles != "КОМАНДА СОБРАНА":
                action_buttons.append(ft.FilledButton("Закрыть набор", on_click=close_project, width=200))
            action_buttons.append(ft.FilledButton("Удалить проект", on_click=delete_project, width=200, bgcolor=ft.Colors.RED_700))
            action_buttons.append(ft.FilledButton("Команда", on_click=lambda e: self.show_project_team(project), width=200))
        elif already_applied:
            action_buttons.append(ft.FilledButton("Отменить заявку", on_click=cancel_application, width=200))
        else:
            action_buttons.append(ft.FilledButton("Отправить заявку", on_click=apply_to_project, width=200))

        content = ft.Column([
            ft.Row([ft.IconButton(ft.Icons.ARROW_BACK, on_click=go_back), ft.Container(expand=True), self.theme_button]),
            ft.Container(expand=True),
            ft.Column([
                ft.Text(project.title, size=32, weight=ft.FontWeight.BOLD),
                ft.Text(f"Автор: {project.user.name if project.user else 'Неизвестный'}", size=16),
                ft.Text(f"Категория: {project.category}", size=16),
                ft.Text(f"Требуемые роли: {project.needed_roles or 'Не указаны'}", size=16),
                ft.Divider(height=20),
                ft.Text("Описание:", size=18, weight=ft.FontWeight.BOLD),
                ft.Text(project.description or "Нет описания", size=14),
                ft.Divider(height=30),
                ft.Row(action_buttons, alignment=ft.MainAxisAlignment.CENTER, spacing=20),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
            ft.Container(expand=True),
        ], expand=True)

        self.clear_and_add(content)

    # ========== СПИСОК УЧАСТНИКОВ ПРОЕКТА ==========
    def show_project_team(self, project):
        team = services.get_project_team(self.session, project.id)

        def go_back(e):
            self.show_project_detail_page(project)

        team_controls = []
        for member in team:
            team_controls.append(
                ft.ListTile(
                    title=ft.Text(member.name, weight=ft.FontWeight.BOLD),
                    subtitle=ft.Text(f"Навыки: {member.skills or 'Не указаны'}"),
                    leading=ft.Icon(ft.Icons.PERSON),
                )
            )

        if not team_controls:
            team_controls.append(ft.Text("В команде пока нет участников", color=ft.Colors.GREY_500))

        self.clear()
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self._create_theme_button()

        content = ft.Column([
            ft.Row([ft.IconButton(ft.Icons.ARROW_BACK, on_click=go_back), ft.Container(expand=True), self.theme_button]),
            ft.Container(expand=True),
            ft.Column([
                ft.Text(f"Команда проекта: {project.title}", size=32, weight=ft.FontWeight.BOLD),
                ft.Divider(height=20),
                ft.Text(f"Участников: {len(team)}", size=16),
                ft.Divider(height=10),
                ft.Column(team_controls, spacing=10),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
            ft.Container(expand=True),
        ], expand=True)

        self.clear_and_add(content)

    # ========== РЕДАКТИРОВАНИЕ ПРОЕКТА ==========
    def edit_project(self, project):
        title_field = ft.TextField(label="Название проекта", value=project.title, width=400)
        desc_field = ft.TextField(label="Описание", value=project.description or "", multiline=True, height=100, width=400)
        category_field = ft.Dropdown(
            label="Категория",
            options=[ft.dropdown.Option(c) for c in ["IT", "Media", "Fashion"]],
            width=400,
            value=project.category
        )
        roles_field = ft.TextField(label="Требуемые роли", value=project.needed_roles or "", width=400)

        error_text = ft.Text("", color=ft.Colors.RED)
        success_text = ft.Text("", color=ft.Colors.GREEN)

        def save_edit(e):
            if not title_field.value:
                error_text.value = "Введите название проекта"
                self.page.update()
                return

            project.title = title_field.value
            project.description = desc_field.value or ""
            project.category = category_field.value
            project.needed_roles = roles_field.value or ""
            self.session.commit()

            success_text.value = "Проект обновлён!"
            error_text.value = ""
            self.page.update()

            import threading
            threading.Timer(1.5, lambda: self.show_my_projects_list()).start()

        def go_back(e):
            self.show_my_projects_list()

        self.clear()
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self._create_theme_button()

        content = ft.Column([
            ft.Row([ft.IconButton(ft.Icons.ARROW_BACK, on_click=go_back), ft.Container(expand=True), self.theme_button]),
            ft.Container(expand=True),
            ft.Column([
                ft.Text("Редактирование проекта", size=32, weight=ft.FontWeight.BOLD),
                ft.Divider(height=10),
                title_field,
                desc_field,
                category_field,
                roles_field,
                ft.Row([
                    ft.FilledButton("Сохранить", on_click=save_edit, width=150),
                    ft.OutlinedButton("Отмена", on_click=go_back, width=150),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
                error_text,
                success_text,
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
            ft.Container(expand=True),
        ], expand=True)

        self.clear_and_add(content)

    # ========== ЭКРАН МОИ ПРОЕКТЫ ==========
    def show_my_projects_list(self):
        self.clear()
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        as_leader = services.get_my_projects(self.session, self.current_user.id)
        as_member = services.get_projects_i_am_in(self.session, self.current_user.id)

        def show_project_details(project):
            self.show_project_detail_page(project)

        leader_controls = []
        for p in as_leader:
            leader_controls.append(
                ft.Row([
                    ft.Container(
                        content=ft.ListTile(
                            title=ft.Text(p.title, weight=ft.FontWeight.BOLD),
                            subtitle=ft.Text(f"Статус: {p.needed_roles}"),
                            on_click=lambda e, proj=p: show_project_details(proj),
                        ),
                        expand=True,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.EDIT,
                        icon_size=20,
                        tooltip="Редактировать",
                        on_click=lambda e, proj=p: self.edit_project(proj),
                    ),
                ])
            )

        leader_expansion = ft.ExpansionTile(
            title=ft.Text(f"Проекты, которыми я руковожу ({len(as_leader)})"),
            controls=leader_controls if as_leader else [ft.Text("Нет проектов", color=ft.Colors.GREY_500)]
        )

        member_expansion = ft.ExpansionTile(
            title=ft.Text(f"Проекты, где я участник ({len(as_member)})"),
            controls=[
                ft.ListTile(title=ft.Text(p.title), subtitle=ft.Text(f"Лидер: {p.user.name}"), on_click=lambda e, proj=p: show_project_details(proj))
                for p in as_member
            ] if as_member else [ft.Text("Нет проектов", color=ft.Colors.GREY_500)]
        )

        self._create_theme_button()

        content = ft.Column([
            ft.Row([ft.IconButton(ft.Icons.HOME, on_click=lambda _: self.show_dashboard()), ft.Container(expand=True), self.theme_button]),
            ft.Container(expand=True),
            ft.Column([
                ft.Text("Мои проекты", size=32, weight=ft.FontWeight.BOLD),
                leader_expansion,
                member_expansion,
                ft.Divider(height=20),
                ft.FilledButton("Создать новый проект", on_click=lambda _: self.show_create_project(), width=250),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
            ft.Container(expand=True),
        ], expand=True)

        self.clear_and_add(content)

    # ========== ЭКРАН ЗАЯВОК ==========
    def show_applications_list(self):
        self.clear()
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        status_filter = ft.Dropdown(
            label="Статус заявок",
            options=[
                ft.dropdown.Option("Все"),
                ft.dropdown.Option("Ожидание"),
                ft.dropdown.Option("Принят"),
                ft.dropdown.Option("Отклонен"),
            ],
            value="Все",
            width=200,
        )

        def load_applications():
            my_apps_query = self.session.query(Application).filter(Application.user_id == self.current_user.id)
            if status_filter.value != "Все":
                my_apps_query = my_apps_query.filter(Application.status == status_filter.value)
            my_apps = my_apps_query.all()

            incoming_apps = self.session.query(Application).join(Project).filter(
                Project.leader_id == self.current_user.id,
                Application.status == "Ожидание"
            ).all()

            def cancel_my_application(app):
                self.session.delete(app)
                self.session.commit()
                self.page.snack_bar = ft.SnackBar(content=ft.Text("Заявка отменена"), bgcolor=ft.Colors.GREEN)
                self.page.snack_bar.open = True
                load_applications()
                self.page.update()

            my_apps_controls = []
            for app in my_apps:
                my_apps_controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text(f"Проект: {app.project.title}", weight=ft.FontWeight.BOLD),
                            ft.Text(f"Статус: {app.status}"),
                            ft.FilledButton("Отменить заявку", on_click=lambda e, a=app: cancel_my_application(a), width=150, bgcolor=ft.Colors.RED_700),
                        ], spacing=10),
                        padding=15,
                        bgcolor=ft.Colors.BLUE_GREY_900 if self.theme_mode == ft.ThemeMode.DARK else ft.Colors.GREY_200,
                        border_radius=10,
                    )
                )

            def accept_application(app):
                services.update_application_status(self.session, app.id, "Принят")
                load_applications()
                self.page.snack_bar = ft.SnackBar(content=ft.Text("Заявка принята"), bgcolor=ft.Colors.GREEN)
                self.page.snack_bar.open = True
                self.page.update()

            def reject_application(app):
                services.update_application_status(self.session, app.id, "Отклонен")
                load_applications()
                self.page.snack_bar = ft.SnackBar(content=ft.Text("Заявка отклонена"), bgcolor=ft.Colors.RED)
                self.page.snack_bar.open = True
                self.page.update()

            incoming_controls = []
            for app in incoming_apps:
                incoming_controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text(f"Проект: {app.project.title}", weight=ft.FontWeight.BOLD),
                            ft.Text(f"От: {app.user.name}"),
                            ft.Text(f"Сообщение: {app.message or 'Без сообщения'}"),
                            ft.Row([
                                ft.FilledButton("Принять", on_click=lambda e, a=app: accept_application(a), width=100, bgcolor=ft.Colors.GREEN),
                                ft.OutlinedButton("Отклонить", on_click=lambda e, a=app: reject_application(a), width=100),
                            ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                        ], spacing=10),
                        padding=15,
                        bgcolor=ft.Colors.BLUE_GREY_900 if self.theme_mode == ft.ThemeMode.DARK else ft.Colors.GREY_200,
                        border_radius=10,
                    )
                )

            self.page.clean()
            self.page.add(
                ft.Column([
                    ft.Row([ft.IconButton(ft.Icons.HOME, on_click=lambda _: self.show_dashboard()), ft.Container(expand=True), self.theme_button]),
                    ft.Column([
                        ft.Text("Заявки", size=32, weight=ft.FontWeight.BOLD),
                        status_filter,
                        ft.ExpansionTile(
                            title=ft.Text(f"Отправленные мной заявки ({len(my_apps)})"),
                            controls=my_apps_controls if my_apps else [ft.Text("Нет заявок", color=ft.Colors.GREY_500)]
                        ),
                        ft.ExpansionTile(
                            title=ft.Text(f"Входящие заявки ({len(incoming_apps)})"),
                            controls=incoming_controls if incoming_apps else [ft.Text("Нет заявок", color=ft.Colors.GREY_500)]
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
                ], expand=True)
            )
            self.page.update()

        status_filter.on_change = lambda e: load_applications()
        self._create_theme_button()

        self.page.clean()
        self.page.add(
            ft.Column([
                ft.Row([ft.IconButton(ft.Icons.HOME, on_click=lambda _: self.show_dashboard()), ft.Container(expand=True), self.theme_button]),
                ft.Column([
                    ft.Text("Заявки", size=32, weight=ft.FontWeight.BOLD),
                    status_filter,
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
            ], expand=True)
        )
        self.page.update()
        load_applications()

    # ========== ЭКРАН СПИСОК ПОЛЬЗОВАТЕЛЕЙ ==========
    def show_users_list(self):
        self.clear()
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        search_field = ft.TextField(
            label="Поиск пользователей",
            hint_text="Введите имя",
            width=400,
        )
        search_result_text = ft.Text("", size=14, color=ft.Colors.GREY_500)
        users_list = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)

        all_users = self.session.query(User).all()

        def load_users():
            users_list.controls.clear()

            query = search_field.value.lower() if search_field.value else ""
            if query:
                filtered = [u for u in all_users if self.matches_search(u.name, query)]
            else:
                filtered = all_users

            filtered = [u for u in filtered if u.id != self.current_user.id]

            if not filtered:
                search_result_text.value = "Пользователей не найдено"
            else:
                search_result_text.value = f"Найдено: {len(filtered)}"
                for u in filtered:
                    users_list.controls.append(
                        ft.Card(
                            content=ft.Container(
                                content=ft.Column([
                                    ft.Text(u.name, size=18, weight=ft.FontWeight.BOLD),
                                    ft.Text(f"Навыки: {u.skills or 'Не указаны'}", size=14, color=ft.Colors.GREY_400),
                                    ft.FilledButton("Подробнее", width=150, on_click=lambda e, user=u: self.show_user_profile_page(user)),
                                ], spacing=8),
                                padding=15,
                            )
                        )
                    )
            self.page.update()

        search_field.on_change = lambda e: load_users()

        self._create_theme_button()

        self.page.clean()
        self.page.add(
            ft.Column([
                ft.Row([ft.IconButton(ft.Icons.HOME, on_click=lambda _: self.show_dashboard()), ft.Container(expand=True), self.theme_button]),
                ft.Column([
                    ft.Text("Пользователи", size=32, weight=ft.FontWeight.BOLD),
                    ft.Row([ft.Container(expand=True), search_field, ft.Container(expand=True)]),
                    ft.Row([ft.Container(expand=True), search_result_text, ft.Container(expand=True)]),
                    ft.Container(content=users_list, width=500),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
            ], expand=True)
        )
        self.page.update()
        load_users()

    # ========== ЭКРАН ПРОФИЛЯ ПОЛЬЗОВАТЕЛЯ ==========
    def show_user_profile_page(self, user):
        self.clear()
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        stats = services.get_user_stats(self.session, user.id)

        as_leader = self.session.query(Project).filter(Project.leader_id == user.id).all()
        as_member = services.get_projects_i_am_in(self.session, user.id)
        all_projects = as_leader + as_member

        def go_back(e):
            self.show_users_list()

        def show_project_details(project):
            self.show_project_detail_page(project)

        projects_controls = []
        for p in all_projects:
            role = "Лидер" if p.leader_id == user.id else "Участник"
            projects_controls.append(
                ft.ListTile(
                    title=ft.Text(p.title, weight=ft.FontWeight.BOLD),
                    subtitle=ft.Text(f"Роль: {role} | Категория: {p.category}"),
                    on_click=lambda e, proj=p: show_project_details(proj),
                )
            )

        projects_column = ft.Column(projects_controls, spacing=10) if projects_controls else ft.Text("Нет проектов", color=ft.Colors.GREY_500)

        stats_container = ft.Container(
            content=ft.Column([
                ft.Text("Статистика пользователя", size=16, weight=ft.FontWeight.BOLD),
                ft.Text(f"Веду проектов: {stats['owned']}", size=14),
                ft.Text(f"Участвует: {stats['joined']}", size=14),
                ft.Text(f"Ожидают ответа: {stats['pending']}", size=14),
            ], spacing=5),
            padding=15,
            bgcolor=ft.Colors.BLUE_GREY_900 if self.theme_mode == ft.ThemeMode.DARK else ft.Colors.GREY_200,
            border_radius=10,
        )

        self._create_theme_button()

        content = ft.Column([
            ft.Row([ft.IconButton(ft.Icons.ARROW_BACK, on_click=go_back), ft.Container(expand=True), self.theme_button]),
            ft.Container(expand=True),
            ft.Column([
                ft.Text(user.name, size=32, weight=ft.FontWeight.BOLD),
                ft.Text(f"ID: {user.id}", size=14, color=ft.Colors.GREY_400),
                ft.Text(f"Навыки: {user.skills or 'Не указаны'}", size=16),
                ft.Text(f"О себе: {user.bio or 'Не указано'}", size=14),
                ft.Divider(height=20),
                stats_container,
                ft.Divider(height=20),
                ft.Text("Проекты пользователя:", size=20, weight=ft.FontWeight.BOLD),
                ft.Text(f"Всего проектов: {len(all_projects)}", size=14),
                ft.Divider(height=10),
                projects_column,
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
            ft.Container(expand=True),
        ], expand=True)

        self.clear_and_add(content)

    # ========== ЭКРАН СОЗДАНИЯ ПРОЕКТА ==========
    def show_create_project(self):
        self.clear()
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        title_field = ft.TextField(label="Название проекта", width=400)
        desc_field = ft.TextField(label="Описание", multiline=True, height=100, width=400)
        category_field = ft.Dropdown(
            label="Категория",
            options=[ft.dropdown.Option(c) for c in ["IT", "Media", "Fashion"]],
            width=400,
            value="IT"
        )
        roles_field = ft.TextField(label="Требуемые роли", hint_text="Python, Дизайнер...", width=400)

        error_text = ft.Text("", color=ft.Colors.RED)

        def create(e):
            if not title_field.value:
                error_text.value = "Введите название проекта"
                self.page.update()
                return

            services.create_project(
                self.session,
                title_field.value,
                desc_field.value or "",
                self.current_user.id,
                category_field.value,
                roles_field.value or ""
            )
            self.page.snack_bar = ft.SnackBar(content=ft.Text("Проект создан!"), bgcolor=ft.Colors.GREEN)
            self.page.snack_bar.open = True
            self.show_dashboard()

        self._create_theme_button()

        content = ft.Column([
            ft.Row([ft.IconButton(ft.Icons.HOME, on_click=lambda _: self.show_dashboard()), ft.Container(expand=True), self.theme_button]),
            ft.Container(expand=True),
            ft.Column([
                ft.Text("Создание проекта", size=32, weight=ft.FontWeight.BOLD),
                title_field,
                desc_field,
                category_field,
                roles_field,
                ft.Row([
                    ft.FilledButton("Создать", on_click=create, width=150),
                    ft.OutlinedButton("Отмена", on_click=lambda _: self.show_dashboard(), width=150),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
                error_text,
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
            ft.Container(expand=True),
        ], expand=True)

        self.clear_and_add(content)

    # Запуск приложения
    def run(self, page: ft.Page):
        self.init_db()
        self.setup_page(page)
        self.show_login()


if __name__ == "__main__":
    app = RehubApp()
    ft.app(target=app.run)
