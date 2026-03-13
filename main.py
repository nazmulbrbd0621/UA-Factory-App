import flet as ft
import sqlite3
import os

# --- ড্যাটাবেস সেটআপ ---
# আমরা এখন ডাটাবেসটি main ফাংশনের ভেতর বাটনের চাপে ওপেন করব
class Database:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, stock INTEGER)")
        self.conn.commit()

def main(page: ft.Page):
    page.title = "Sayem Factory Pro"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.ALWAYS
    
    # এটি অ্যাপ ওপেন হওয়ার সাথে সাথে দেখাবে (কনফার্মেশন)
    status_text = ft.Text("App is Running Successfully!", size=20, color="green", weight="bold")
    page.add(status_text)
    
    # এরর লগ দেখার জন্য
    log_text = ft.Text("", color="red")
    page.add(log_text)

    # ড্যাশবোর্ড কন্টেইনার (শুরুতে খালি)
    inventory_list = ft.Column()

    def start_system(e):
        try:
            # অ্যান্ড্রয়েডের জন্য সবচেয়ে নিরাপদ এবং পারমিশন-ফ্রি পাথ
            # এটি ইন্টারনাল ডাটা ফোল্ডার ব্যবহার করবে
            data_dir = page.client_storage.get("path") # ট্রাই করবে
            if not data_dir:
                data_dir = os.path.join(os.path.expanduser("~"), "sayem_data")
            
            if not os.path.exists(data_dir):
                os.makedirs(data_dir, exist_ok=True)
            
            db_path = os.path.join(data_dir, "factory.db")
            db = Database(db_path)
            
            # ডাটাবেস কানেক্ট হলে ইউআই আপডেট
            db.cursor.execute("INSERT INTO products (name, stock) VALUES (?, ?)", ("Test Product", 100))
            db.conn.commit()
            
            status_text.value = "Database Connected & Record Added!"
            status_text.color = "blue"
            
            db.cursor.execute("SELECT * FROM products")
            rows = db.cursor.fetchall()
            inventory_list.controls.clear()
            for r in rows:
                inventory_list.controls.append(ft.Text(f"Product: {r[1]} - Stock: {r[2]}"))
            
            page.update()
            
        except Exception as err:
            log_text.value = f"Error: {str(err)}"
            page.update()

    # মেইন স্ক্রিন বাটন
    page.add(
        ft.ElevatedButton("Connect Database & Test Logic", on_click=start_system, height=50),
        ft.Divider(),
        ft.Text("Inventory Results:", size=16, weight="bold"),
        inventory_list
    )
    
    page.update()

ft.app(target=main)
