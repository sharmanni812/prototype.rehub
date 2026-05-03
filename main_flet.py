import flet as ft
from app import db_session, services
from app.tables import User


class RehubApp:
    """Главный класс приложения REHUB"""
    
    def __init__(self):
        self.session = None
        self.current_user = None
        self.theme_mode = ft.ThemeMode.DARK
        self.page = None
        
        # UI компоненты
        self.theme_button = None
        self.settings_button = None
        self.exit_button = None
    
    # ========== ИНИЦИАЛИЗАЦИЯ ==========
    def init_db(self):
        """Инициализация базы данных"""
        db_session.global_init("db/projects.db")
        self.session = db_session.create_session()
    
    def setup_page(self, page: ft.Page):
        """Настройка главной страницы"""
        self.page = page
        page.title = "REHUB"
        page.theme_mode = self.theme_mode
        page.window_width = 500
        page.window_height = 700
        page.padding = 20
        page.scroll = ft.ScrollMode.AUTO
        self._create_buttons()
    
    def _create_buttons(self):
        """Создание общих кнопок"""
        self.theme_button = ft.IconButton(
            icon=ft.Icons.DARK_MODE,
            icon_size=30,
            on_click=self.toggle_theme,
            tooltip="Сменить тему",
        )
        self.settings_button = ft.IconButton(
            icon=ft.Icons.SETTINGS,
            icon_size=30,
            tooltip="Настройки",
        )
        self.exit_button = ft.IconButton(
            icon=ft.Icons.EXIT_TO_APP,
            icon_size=30,
            on_click=self.exit_app,
            tooltip="Выйти",
        )
    
    # ========== ОБЩИЕ МЕТОДЫ ==========
    def toggle_theme(self, e):
        """Переключение темы"""
        if self.theme_mode == ft.ThemeMode.DARK:
            self.theme_mode = ft.ThemeMode.LIGHT
            self.page.theme_mode = ft.ThemeMode.LIGHT
            self.theme_button.icon = ft.Icons.LIGHT_MODE
        else:
            self.theme_mode = ft.ThemeMode.DARK
            self.page.theme_mode = ft.ThemeMode.DARK
            self.theme_button.icon = ft.Icons.DARK_MODE
        self.page.update()
    
    def exit_app(self, e):
        """Выход из приложения"""
        raise SystemExit(0)
    
    def clear_and_add(self, content):
        """Очистка страницы и добавление нового контента"""
        self.page.clean()
        self.page.add(content)
        self.page.update()
    
    # ========== ЛОГИКА РАБОТЫ С ПОЛЬЗОВАТЕЛЯМИ ==========
    def names_equal(self, name1, name2):
        """Сравнение имён (первая буква без учёта регистра)"""
        if len(name1) != len(name2):
            return False
        if name1[0].lower() != name2[0].lower():
            return False
        return name1[1:] == name2[1:]
    
    def is_name_unique(self, name, exclude_user_id=None):
        """Проверка уникальности имени"""
        all_users = self.session.query(User).all()
        for user in all_users:
            if exclude_user_id and user.id == exclude_user_id:
                continue
            if self.names_equal(user.name, name):
                return False
        return True
    
    def smart_login(self, login_input):
        """Умный вход (email, ID или имя)"""
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
    
    def update_user_profile(self, user_id, name=None, email=None, bio=None, skills=None):
        """Обновление профиля пользователя с проверками"""
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
    
    # ========== ЭКРАНЫ ==========
    def show_login(self):
        """Экран входа"""
        login_field = ft.TextField(label="Email или ID", width=300, autofocus=True)
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
        
        content = ft.Column([
            ft.Row([ft.Container(expand=True), self.exit_button]),
            ft.Container(expand=True),
            ft.Column([
                ft.Text("REHUB", size=48, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_400),
                ft.Text("Вход в систему", size=20),
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                login_field,
                ft.ElevatedButton("Войти", on_click=do_login, width=300),
                ft.TextButton("Нет аккаунта? Зарегистрироваться", on_click=lambda _: self.show_register()),
                error_text,
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
            ft.Container(expand=True),
            ft.Row([ft.Container(expand=True), self.theme_button], alignment=ft.MainAxisAlignment.END),
        ], expand=True)
        
        self.clear_and_add(content)
    
    def show_register(self):
        """Экран регистрации"""
        name_field = ft.TextField(label="Имя", width=300)
        email_field = ft.TextField(label="Email", width=300)
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
        
        content = ft.Column([
            ft.Row([ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: self.show_login()), ft.Container(expand=True)]),
            ft.Container(expand=True),
            ft.Column([
                ft.Text("Регистрация", size=32, weight=ft.FontWeight.BOLD),
                ft.Text("Нужны только имя и email", size=12, color=ft.Colors.GREY_500),
                name_field,
                email_field,
                ft.ElevatedButton("Зарегистрироваться", on_click=do_register, width=300),
                reg_error,
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
            ft.Container(expand=True),
            ft.Row([ft.Container(expand=True), self.theme_button], alignment=ft.MainAxisAlignment.END),
        ], expand=True)
        
        self.clear_and_add(content)
    
    def show_dashboard(self):
        """Главный экран (дашборд)"""
        search_field = ft.TextField(
            label="Поиск проектов",
            hint_text="Введите название или описание",
            width=300,
        )
        search_result_text = ft.Text("", size=14, color=ft.Colors.GREY_500)
        
        def do_search(e):
            query = search_field.value
            if not query:
                search_result_text.value = "Введите текст для поиска"
            else:
                search_result_text.value = f"Поиск по запросу: '{query}'\nРезультатов не найдено"
            self.page.update()
        
        search_field.on_submit = do_search
        search_field.suffix = ft.IconButton(ft.Icons.SEARCH, on_click=do_search, tooltip="Искать")
        
        self.settings_button.on_click = lambda _: self.show_settings()
        
        content = ft.Column([
            ft.Row([ft.Container(expand=True), self.settings_button]),
            ft.Container(expand=True),
            ft.Column([
                ft.Text(f"Добро пожаловать, {self.current_user.name}!", size=28, weight=ft.FontWeight.BOLD),
                ft.Text(f"{self.current_user.email}", size=14, color=ft.Colors.GREY_400),
                ft.Text(f"ID: {self.current_user.id}", size=12, color=ft.Colors.GREY_500),
                ft.Divider(height=20),
                search_field,
                search_result_text,
                ft.Divider(height=20),
                ft.ElevatedButton("Создать новый проект", on_click=lambda _: self.show_create_project(), width=250),
                ft.ElevatedButton("Мои проекты", on_click=lambda _: self.show_my_projects(), width=250),
                ft.Divider(height=10),
                ft.ElevatedButton(
                    "Выйти из аккаунта", 
                    on_click=lambda _: self.show_login(), 
                    width=250, 
                    bgcolor=ft.Colors.RED_700, 
                    color=ft.Colors.WHITE
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
            ft.Container(expand=True),
            ft.Row([ft.Container(expand=True), self.theme_button], alignment=ft.MainAxisAlignment.END),
        ], expand=True)
        
        self.clear_and_add(content)
    
    def show_create_project(self):
        """Экран создания проекта (заглушка)"""
        def go_back(e):
            self.show_dashboard()
        
        content = ft.Column([
            ft.Row([ft.IconButton(ft.Icons.ARROW_BACK, on_click=go_back), ft.Container(expand=True), self.settings_button]),
            ft.Container(expand=True),
            ft.Column([
                ft.Text("Создание проекта", size=32, weight=ft.FontWeight.BOLD),
                ft.Text("Эта функция будет добавлена позже", size=16, color=ft.Colors.GREY_500),
                ft.ElevatedButton("Назад", on_click=go_back, width=200),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20),
            ft.Container(expand=True),
            ft.Row([ft.Container(expand=True), self.theme_button], alignment=ft.MainAxisAlignment.END),
        ], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        self.clear_and_add(content)
    
    def show_my_projects(self):
        """Экран моих проектов (заглушка)"""
        def go_back(e):
            self.show_dashboard()
        
        content = ft.Column([
            ft.Row([ft.IconButton(ft.Icons.ARROW_BACK, on_click=go_back), ft.Container(expand=True), self.settings_button]),
            ft.Container(expand=True),
            ft.Column([
                ft.Text("Мои проекты", size=32, weight=ft.FontWeight.BOLD),
                ft.Text("Список проектов будет здесь", size=16, color=ft.Colors.GREY_500),
                ft.ElevatedButton("Назад", on_click=go_back, width=200),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20),
            ft.Container(expand=True),
            ft.Row([ft.Container(expand=True), self.theme_button], alignment=ft.MainAxisAlignment.END),
        ], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        self.clear_and_add(content)
    
    def show_settings(self):
        """Экран настроек (профиль)"""
        stats = services.get_user_stats(self.session, self.current_user.id)
        stats_bg = ft.Colors.BLUE_GREY_900 if self.theme_mode == ft.ThemeMode.DARK else ft.Colors.BLUE_GREY_100
        stats_color = ft.Colors.WHITE if self.theme_mode == ft.ThemeMode.DARK else ft.Colors.BLACK
        
        name_field = ft.TextField(label="Имя", value=self.current_user.name, width=300)
        email_field = ft.TextField(label="Email", value=self.current_user.email, width=300)
        skills_field = ft.TextField(label="Навыки", value=self.current_user.skills or "", width=300)
        bio_field = ft.TextField(label="О себе", value=self.current_user.bio or "", multiline=True, height=60, width=300)
        
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
        
        content = ft.Column([
            ft.Row([ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: self.show_dashboard()), ft.Container(expand=True)]),
            ft.Container(expand=True),
            ft.Column([
                ft.Text("Настройки", size=32, weight=ft.FontWeight.BOLD),
                name_field,
                email_field,
                skills_field,
                bio_field,
                ft.Row([
                    ft.ElevatedButton("Сохранить", on_click=save_profile, width=140),
                    ft.OutlinedButton("Отмена", on_click=lambda _: self.show_dashboard(), width=140),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
                save_status,
                error_status,
                ft.Divider(height=20),
                ft.Text("Статистика", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Column([
                        ft.Text(f"Веду проектов: {stats['owned']}", size=14, color=stats_color),
                        ft.Text(f"Участвую: {stats['joined']}", size=14, color=stats_color),
                        ft.Text(f"Ожидают ответа: {stats['pending']}", size=14, color=stats_color),
                    ], spacing=8),
                    padding=15,
                    bgcolor=stats_bg,
                    border_radius=12,
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12),
            ft.Container(expand=True),
            ft.Row([ft.Container(expand=True), self.theme_button], alignment=ft.MainAxisAlignment.END),
        ], expand=True)
        
        self.clear_and_add(content)
    
    def run(self, page: ft.Page):
        """Запуск приложения"""
        self.init_db()
        self.setup_page(page)
        self.show_login()


if __name__ == "__main__":
    app = RehubApp()
    ft.app(target=app.run)
