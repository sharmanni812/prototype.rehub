import flet as ft
from app import db_session, services
from app.tables import User

# Инициализация БД
db_session.global_init("db/projects.db")
session = db_session.create_session()
current_user = None


def main(page: ft.Page):
    page.title = "REHUB"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 500
    page.window_height = 600
    page.padding = 20
    
    theme_mode = ft.ThemeMode.DARK
    
    # Функция смены темы
    def toggle_theme(e):
        nonlocal theme_mode
        if theme_mode == ft.ThemeMode.DARK:
            theme_mode = ft.ThemeMode.LIGHT
            page.theme_mode = ft.ThemeMode.LIGHT
            theme_button.icon = ft.Icons.LIGHT_MODE
        else:
            theme_mode = ft.ThemeMode.DARK
            page.theme_mode = ft.ThemeMode.DARK
            theme_button.icon = ft.Icons.DARK_MODE
        page.update()
    
    # Кнопка темы
    theme_button = ft.IconButton(
        icon=ft.Icons.DARK_MODE,
        icon_size=30,
        on_click=toggle_theme,
        tooltip="Сменить тему",
    )
    
    # Умный вход
    def smart_login(login_input):
        value = login_input.strip()
        
        if value.isdigit():
            user = services.authenticate_user(session, value)
            if user:
                return user
        
        user = session.query(User).filter(User.email == value).first()
        if user:
            return user
        
        return None
    
    # Поля для входа
    login_field = ft.TextField(
        label="Email или ID", 
        width=300, 
        autofocus=True,
        hint_text="Введите email или номер ID"
    )
    error_text = ft.Text("", color=ft.Colors.RED)
    
    def do_login(e):
        global current_user
        user = smart_login(login_field.value)
        
        if user:
            current_user = user
            show_dashboard()
        else:
            error_text.value = "Пользователь не найден"
            page.update()
    
    # Экран регистрации
    def show_register():
        page.clean()
        
        name_field = ft.TextField(label="Имя", width=300)
        email_field_reg = ft.TextField(label="Email", width=300)
        reg_error = ft.Text("", color=ft.Colors.RED)
        success_text = ft.Text("", color=ft.Colors.GREEN)
        
        def do_register(e):
            if not name_field.value or not email_field_reg.value:
                reg_error.value = "Заполните имя и email"
                page.update()
                return
            
            if "@" not in email_field_reg.value or "." not in email_field_reg.value:
                reg_error.value = "Введите корректный email"
                page.update()
                return
            
            existing = session.query(User).filter(User.email == email_field_reg.value).first()
            if existing:
                reg_error.value = "Этот email уже зарегистрирован"
                page.update()
                return
            
            user = services.create_user(
                session, 
                name_field.value, 
                email_field_reg.value,
                bio="",
                skills=""
            )
            
            success_text.value = f"Аккаунт создан! Ваш ID: {user.id}"
            reg_error.value = ""
            page.update()
            
            import threading
            threading.Timer(2, lambda: show_login()).start()
        
        def go_back(e):
            show_login()
        
        center_content = ft.Column([
            ft.Text("Регистрация", size=32, weight=ft.FontWeight.BOLD),
            ft.Text("Нужны только имя и email", size=12, color=ft.Colors.GREY_500),
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            name_field,
            email_field_reg,
            ft.ElevatedButton("Зарегистрироваться", on_click=do_register, width=300),
            ft.TextButton("Назад к входу", on_click=go_back),
            reg_error,
            success_text,
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15)
        
        page.add(
            ft.Container(
                content=ft.Column([
                    ft.Container(expand=True),
                    ft.Row([
                        ft.Container(expand=True),
                        center_content,
                        ft.Container(expand=True),
                    ]),
                    ft.Container(expand=True),
                    ft.Row([
                        ft.Container(expand=True),
                        theme_button,
                    ]),
                ], expand=True),
                expand=True
            )
        )
        page.update()
    
    # Дашборд
    def show_dashboard():
        page.clean()
        stats = services.get_user_stats(session, current_user.id)
        
        center_content = ft.Column([
            ft.Text(f"Добро пожаловать, {current_user.name}!", size=28, weight=ft.FontWeight.BOLD),
            ft.Text(f"{current_user.email}", size=14, color=ft.Colors.GREY_400),
            ft.Text(f"ID: {current_user.id}", size=12, color=ft.Colors.GREY_500),
            ft.Divider(height=20),
            ft.Container(
                content=ft.Column([
                    ft.Text(f"Веду проектов: {stats['owned']}", size=16),
                    ft.Text(f"Участвую: {stats['joined']}", size=16),
                    ft.Text(f"Ожидают ответа: {stats['pending']}", size=16),
                ], spacing=10),
                padding=20,
                bgcolor=ft.Colors.BLUE_GREY_900 if page.theme_mode == ft.ThemeMode.DARK else ft.Colors.GREY_200,
                border_radius=15,
            ),
            ft.Divider(height=20),
            ft.ElevatedButton("Выйти", on_click=lambda _: show_login(), width=200),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15)
        
        page.add(
            ft.Container(
                content=ft.Column([
                    ft.Container(expand=True),
                    ft.Row([
                        ft.Container(expand=True),
                        center_content,
                        ft.Container(expand=True),
                    ]),
                    ft.Container(expand=True),
                    ft.Row([
                        ft.Container(expand=True),
                        theme_button,
                    ]),
                ], expand=True),
                expand=True
            )
        )
        page.update()
    
    # Экран входа
    def show_login():
        page.clean()
        
        login_field.value = ""
        error_text.value = ""
        
        center_content = ft.Column([
            ft.Text("REHUB", size=48, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_400),
            ft.Text("Вход в систему", size=20),
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            login_field,
            ft.ElevatedButton("Войти", on_click=do_login, width=300),
            ft.TextButton("Нет аккаунта? Зарегистрироваться", on_click=lambda _: show_register()),
            error_text,
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15)
        
        page.add(
            ft.Container(
                content=ft.Column([
                    ft.Container(expand=True),
                    ft.Row([
                        ft.Container(expand=True),
                        center_content,
                        ft.Container(expand=True),
                    ]),
                    ft.Container(expand=True),
                    ft.Row([
                        ft.Container(expand=True),
                        theme_button,
                    ]),
                ], expand=True),
                expand=True
            )
        )
        page.update()
    
    # Запуск
    show_login()


if __name__ == "__main__":
    ft.app(target=main)
