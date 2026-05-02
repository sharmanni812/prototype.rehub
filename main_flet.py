import flet as ft
from app import db_session, services

db_session.global_init("db/projects.db")
session = db_session.create_session()
current_user = None


def main(page: ft.Page):
    page.title = "REHUB"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 450
    page.window_height = 500
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    
    id_field = ft.TextField(label="Ваш ID", width=300, autofocus=True)
    error_text = ft.Text("", color=ft.Colors.RED)
    
    def show_dashboard():
        """Показать дашборд после входа"""
        page.clean()
        stats = services.get_user_stats(session, current_user.id)
        
        page.add(
            ft.Column([
                ft.Text(f"Добро пожаловать, {current_user.name}!", size=28, weight=ft.FontWeight.BOLD),
                ft.Text(f" Веду проектов: {stats['owned']}", size=16),
                ft.Text(f" Участвую: {stats['joined']}", size=16),
                ft.Text(f" Ожидают ответа: {stats['pending']}", size=16),
                ft.Divider(height=30),
                ft.ElevatedButton(" Выйти", on_click=lambda _: show_login()),
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15)
        )
        page.update()
    
    def show_login():
        """Показать экран входа"""
        nonlocal id_field, error_text
        page.clean()
        id_field.value = ""
        error_text.value = ""
        
        page.add(
            ft.Column([
                ft.Text("REHUB", size=48, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_400),
                ft.Text("Вход в систему", size=20),
                id_field,
                ft.ElevatedButton("Войти", on_click=do_login, width=300),
                ft.TextButton("Регистрация", on_click=lambda _: show_register()),
                error_text,
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15)
        )
        page.update()
    
    def do_login(e):
        global current_user
        user = services.authenticate_user(session, id_field.value)
        if user:
            current_user = user
            show_dashboard()
        else:
            error_text.value = " Пользователь не найден"
            page.update()
    
    def show_register():
        page.clean()
        
        name_field = ft.TextField(label="Имя", width=300)
        email_field = ft.TextField(label="Email", width=300)
        reg_error = ft.Text("", color=ft.Colors.RED)
        
        def do_register(e):
            global current_user
            if not name_field.value or not email_field.value:
                reg_error.value = " Заполните имя и email"
                page.update()
                return
            
            user = services.create_user(session, name_field.value, email_field.value)
            current_user = user
            show_dashboard()
        
        page.add(
            ft.Column([
                ft.Text("Регистрация", size=32, weight=ft.FontWeight.BOLD),
                name_field,
                email_field,
                ft.ElevatedButton("Зарегистрироваться", on_click=do_register, width=300),
                ft.TextButton("← Назад", on_click=lambda _: show_login()),
                reg_error,
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15)
        )
        page.update()
    
    show_login()


if __name__ == "__main__":
    ft.app(target=main)
