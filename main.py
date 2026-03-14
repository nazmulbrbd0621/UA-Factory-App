import flet as ft
import sqlite3
import os

class Database:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, stock INTEGER)")
        self.conn.commit()

def main(page: ft.Page):
    page.title = "UA Factory Pro"
    page.theme_mode = ft.ThemeMode.LIGHT
    
    try:
        # অ্যান্ড্রয়েডের জন্য সেফ পাথ
        u_dir = getattr(page, "user_data_dir", None)
        if not u_dir:
            u_dir = os.path.expanduser("~")
            
        if not os.path.exists(u_dir):
            os.makedirs(u_dir, exist_ok=True)
            
        db_file = os.path.join(u_dir, "factory_test.db")
        db = Database(db_file)
        
        page.add(
            ft.AppBar(title=ft.Text("Sayem Factory Dashboard"), bgcolor=ft.colors.BLUE_800, color="white"),
            ft.Container(
                padding=20,
                content=ft.Column([
                    ft.Text("Success! App is running on Android.", size=20, color="green", weight="bold"),
                    ft.Text(f"Database Path: {u_dir}", size=12),
                    ft.ElevatedButton("Add Sample Product", on_click=lambda _: page.add(ft.Text("Product Added!")))
                ])
            )
        )
    except Exception as e:
        page.add(ft.Text(f"Startup Error: {e}", color="red", size=20))

ft.app(target=main)
