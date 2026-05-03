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
        page.window_width = 850
        page.window_height = 700
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

    # Проверка уникальности имени
    def is_name_unique(self, name, exclude_user_id=None):
        all_users = self.session.query(User).all()
        for user in all_users:
            if exclude_user_id and user.id == exclude_user_id:
                continue
            if self.names_equal(user.name, name):
                return False
        return True

    # Умный вход (email, ID или имя)
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

    # Обновление профиля с проверками
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

    # Экран входа
    def show_login(self):
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

    # Экран регистрации
    def show_register(self):
        name_field = ft.TextField(label="Имя", width=400)
        email_field = ft.TextField(label="Email", width=400)
        reg_error = ft.Text("", color=ft.Colors.RED)

        def do_register(e):
            if not name_field.value or not email_field.value:
                reg_error.value = "Заполните имя и email"
                self.page.update()
                return
            if len(name_field.value.strip()) < 2:
                reg_error.value = "Имя должно содержать хотя бы 2 символа"
                self.page.update()
                return
            if "@" not in email_field.value or "." not in email_field.value:
                reg_error.value = "Введите корректный email"
                self.page.update()
                return
            if not self.is_name_unique(name_field.value):
                reg_error.value = "Это имя уже занято"
                self.page.update()
                return

            existing_email = self.session.query(User).filter(User.email == email_field.value).first()
            if existing_email:
                reg_error.value = "Этот email уже зарегистрирован"
                self.page.update()
                return

            user = services.create_user(
                self.session,
                name_field.value.strip(),
                email_field.value.strip(),
                bio="",
                skills=""
            )
            self.current_user = user
            self.show_dashboard()

        self._create_theme_button()

        content = ft.Column([
            ft.Row([ft.IconButton(ft.Icons.HOME, on_click=lambda _: self.show_dashboard()), ft.Container(expand=True), self.theme_button]),
            ft.Container(expand=True),
            ft.Column([
                ft.Text("Регистрация", size=32, weight=ft.FontWeight.BOLD),
                ft.Text("Нужны только имя и email", size=12, color=ft.Colors.GREY_500),
                name_field,
                email_field,
                ft.FilledButton("Зарегистрироваться", on_click=do_register, width=400),
                reg_error,
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
            ft.Container(expand=True),
        ], expand=True)

        self.clear_and_add(content)

    # Дашборд
    def show_dashboard(self):
        self._create_theme_button()

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
            ft.TextButton("Профиль", icon=ft.Icons.PERSON, on_click=lambda _: self.show_settings(), width=150),
            ft.TextButton("Найти проект", icon=ft.Icons.SEARCH, on_click=lambda _: self.show_find_projects(), width=150),
            ft.TextButton("Мои проекты", icon=ft.Icons.FOLDER, on_click=lambda _: self.show_my_projects_list(), width=150),
            ft.TextButton("Заявки", icon=ft.Icons.LIST_ALT, on_click=lambda _: self.show_applications_list(), width=150),
        ], spacing=10)

        search_functions = ft.TextField(
            hint_text="Поиск...",
            width=300,
            on_change=self.search_functions
        )

        right_panel = ft.Column([
            ft.Text(f"Приветствие, {self.current_user.name}!", size=24, weight=ft.FontWeight.BOLD),
            ft.Text(f"ID: {self.current_user.id}", size=14, color=ft.Colors.GREY_400),
            ft.Divider(height=20),
            search_functions,
        ], spacing=15)

        self.suggestions_column = ft.Column(spacing=5)
        self.fixed_height_container = ft.Container(
            content=self.suggestions_column,
            height=150,
            visible=True
        )

        right_panel_full = ft.Column([
            right_panel,
            self.fixed_height_container,
        ], spacing=10)

        content = ft.Row([
            ft.Container(nav_menu, width=180),
            ft.VerticalDivider(width=1),
            ft.Container(right_panel_full, expand=True, padding=20),
        ], expand=True)

        self.clear_and_add(ft.Column([top_bar, content], expand=True))

    # Поиск по функциям
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
        }

        suggestions = []
        if query:
            for key, func in functions.items():
                if query in key:
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

    # Экран настроек
    def show_settings(self):
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
                    # Удаляем заявки пользователя
                    self.session.query(Application).filter(Application.user_id == self.current_user.id).delete()
                    # Удаляем проекты пользователя и связанные заявки
                    my_projects = self.session.query(Project).filter(Project.leader_id == self.current_user.id).all()
                    for p in my_projects:
                        self.session.query(Application).filter(Application.project_id == p.id).delete()
                        self.session.delete(p)
                    # Удаляем пользователя
                    self.session.delete(self.current_user)
                    self.session.commit()
                    
                    self.page.snack_bar = ft.SnackBar(content=ft.Text("Аккаунт удалён"), bgcolor=ft.Colors.GREEN)
                    self.page.snack_bar.open = True
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

    # Экран поиска проектов
    def show_find_projects(self):
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

        # Получаем все проекты один раз
        all_projects = self.session.query(Project).all()
        # Получаем заявки текущего пользователя
        user_applications = {app.project_id for app in self.session.query(Application).filter(Application.user_id == self.current_user.id).all()}

        def load_projects():
            projects_list.controls.clear()
            
            # Сначала фильтруем по категории
            if category_filter.value == "Все":
                filtered = all_projects.copy()
            else:
                filtered = [p for p in all_projects if p.category == category_filter.value]
            
            # Потом фильтруем по поиску
            query = search_field.value.lower() if search_field.value else ""
            if query:
                filtered = [p for p in filtered if query in p.title.lower() or (p.description and query in p.description.lower())]
            
            if not filtered:
                search_result_text.value = "Проектов не найдено"
            else:
                search_result_text.value = f"Найдено: {len(filtered)}"
                for p in filtered:
                    # Проверяем, отправлял ли пользователь заявку
                    already_applied = p.id in user_applications
                    is_own_project = p.leader_id == self.current_user.id
                    
                    if is_own_project:
                        button_text = "Ваш проект"
                        button_disabled = True
                    elif already_applied:
                        button_text = "Заявка отправлена"
                        button_disabled = True
                    else:
                        button_text = "Подробнее"
                        button_disabled = False
                    
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

        # При изменении категории или поиска обновляем список
        def on_category_change(e):
            load_projects()
        
        def on_search_change(e):
            load_projects()

        category_filter.on_change = on_category_change
        search_field.on_change = on_search_change
        search_field.on_submit = on_search_change
        
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

    # Экран деталей проекта
    def show_project_detail_page(self, project):
        # Проверяем, отправлял ли пользователь заявку
        already_applied = self.session.query(Application).filter(
            Application.user_id == self.current_user.id,
            Application.project_id == project.id
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

        def go_back(e):
            self.show_find_projects()

        self.clear()
        
        # Кнопка отправки заявки видна только если проект не свой и заявка не отправлена
        apply_button = None
        if not is_own_project and not already_applied:
            apply_button = ft.FilledButton("Отправить заявку", on_click=apply_to_project, width=300)
        elif already_applied:
            apply_button = ft.FilledButton("Заявка уже отправлена", disabled=True, width=300)
        elif is_own_project:
            apply_button = ft.FilledButton("Это ваш проект", disabled=True, width=300)
        
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
                apply_button if apply_button else ft.Text(""),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
            ft.Container(expand=True),
        ], expand=True)
        
        self.clear_and_add(content)

    # Экран мои проекты
    def show_my_projects_list(self):
        as_leader = services.get_my_projects(self.session, self.current_user.id)
        as_member = services.get_projects_i_am_in(self.session, self.current_user.id)

        def show_project_details(project):
            dialog = ft.AlertDialog(
                title=ft.Text(project.title),
                content=ft.Container(
                    content=ft.Column([
                        ft.Text(f"Автор: {project.user.name}"),
                        ft.Text(f"Категория: {project.category}"),
                        ft.Text(f"Роли: {project.needed_roles or 'Не указаны'}"),
                        ft.Divider(),
                        ft.Text("Описание:", weight=ft.FontWeight.BOLD),
                        ft.Text(project.description or "Нет описания"),
                    ], spacing=10),
                    width=500,
                    height=400,
                ),
                actions=[ft.TextButton("Закрыть", on_click=lambda e: setattr(dialog, "open", False))]
            )
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()

        leader_expansion = ft.ExpansionTile(
            title=ft.Text(f"Проекты, которыми я руковожу ({len(as_leader)})"),
            controls=[
                ft.ListTile(title=ft.Text(p.title), subtitle=ft.Text(f"Статус: {p.needed_roles}"), on_click=lambda e, proj=p: show_project_details(proj))
                for p in as_leader
            ] if as_leader else [ft.Text("Нет проектов", color=ft.Colors.GREY_500)]
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

    # Экран заявок
    def show_applications_list(self):
        my_apps = self.session.query(Application).filter(Application.user_id == self.current_user.id).all()
        incoming_apps = self.session.query(Application).join(Project).filter(
            Project.leader_id == self.current_user.id,
            Application.status == "Ожидание"
        ).all()

        my_apps_expansion = ft.ExpansionTile(
            title=ft.Text(f"Отправленные мной заявки ({len(my_apps)})"),
            controls=[
                ft.ListTile(
                    title=ft.Text(app.project.title),
                    subtitle=ft.Text(f"Статус: {app.status}"),
                )
                for app in my_apps
            ] if my_apps else [ft.Text("Нет заявок", color=ft.Colors.GREY_500)]
        )

        def accept_application(app):
            services.update_application_status(self.session, app.id, "Принят")
            self.show_applications_list()
            self.page.snack_bar = ft.SnackBar(content=ft.Text("Заявка принята"), bgcolor=ft.Colors.GREEN)
            self.page.snack_bar.open = True
            self.page.update()

        def reject_application(app):
            services.update_application_status(self.session, app.id, "Отклонен")
            self.show_applications_list()
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

        incoming_expansion = ft.ExpansionTile(
            title=ft.Text(f"Входящие заявки ({len(incoming_apps)})"),
            controls=incoming_controls if incoming_apps else [ft.Text("Нет заявок", color=ft.Colors.GREY_500)]
        )

        self._create_theme_button()

        content = ft.Column([
            ft.Row([ft.IconButton(ft.Icons.HOME, on_click=lambda _: self.show_dashboard()), ft.Container(expand=True), self.theme_button]),
            ft.Container(expand=True),
            ft.Column([
                ft.Text("Заявки", size=32, weight=ft.FontWeight.BOLD),
                my_apps_expansion,
                incoming_expansion,
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
            ft.Container(expand=True),
        ], expand=True)

        self.clear_and_add(content)

    # Экран создания проекта
    def show_create_project(self):
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
