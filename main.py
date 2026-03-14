import flet as ft
import sqlite3
import os
from datetime import datetime

# --- ড্যাটাবেস ক্লাস ---
class Database:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, stock INTEGER, price REAL)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS customers (id INTEGER PRIMARY KEY, name TEXT, phone TEXT)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS sales_log (id INTEGER PRIMARY KEY, customer_name TEXT, product_name TEXT, qty INTEGER, total REAL, date TEXT)")
        self.conn.commit()

def main(page: ft.Page):
    # ১. সুপার সেফ পাথ লজিক (যা আর এরর দিবে না)
    try:
        # যদি user_data_dir থাকে তবে সেটি নিবে, না থাকলে ওএস অনুযায়ী পাথ সেট করবে
        working_dir = getattr(page, "user_data_dir", None)
        if not working_dir:
            if os.name == 'nt':
                working_dir = os.path.join(os.getcwd(), "data")
            else:
                working_dir = os.path.expanduser("~") # Android Safe Fallback

        if not os.path.exists(working_dir):
            os.makedirs(working_dir, exist_ok=True)
            
        db_file = os.path.join(working_dir, "factory_v10.db")
        db = Database(db_file)
    except Exception as e:
        page.add(ft.Text(f"Critical Startup Error: {e}", color="red", size=20))
        page.update()
        return

    page.title = "UA Factory Pro"
    page.theme_mode = ft.ThemeMode.LIGHT

    # --- নেভিগেশন ---
    def go_back(e):
        if len(page.views) > 1:
            page.views.pop()
            page.go(page.views[-1].route)

    # --- পেজ ভিউ লজিক ---
    def route_change(e):
        page.views.clear()
        
        # ১. ড্যাশবোর্ড
        if page.route == "/":
            db.cursor.execute("SELECT name, stock FROM products")
            rows = db.cursor.fetchall()
            
            grid = ft.GridView(expand=False, runs_count=2, child_aspect_ratio=2.2, spacing=10)
            for r in rows:
                c = ft.colors.GREEN_400 if r[1] > 15 else ft.colors.RED_400
                grid.controls.append(
                    ft.Container(padding=10, border_radius=10, bgcolor=ft.colors.BLUE_GREY_50,
                        content=ft.Column([
                            ft.Text(r[0], size=12, weight="bold", no_wrap=True),
                            ft.Text(f"{r[1]} Pcs", size=15, color=c, weight="bold")
                        ], horizontal_alignment="center"))
                )

            page.views.append(ft.View("/", [
                ft.AppBar(title=ft.Text("Sayem Factory"), bgcolor=ft.colors.BLUE_800, color="white"),
                ft.Container(padding=15, content=ft.Column([
                    ft.Text("Inventory Status", size=18, weight="bold"),
                    grid,
                    ft.Divider(),
                    ft.Row([
                        ft.ElevatedButton("Stock", icon=ft.icons.STORAGE, on_click=lambda _: page.go("/inventory"), expand=True),
                        ft.ElevatedButton("New Sale", icon=ft.icons.SHOPPING_CART, on_click=lambda _: page.go("/sales"), expand=True, bgcolor=ft.colors.GREEN_700, color="white"),
                    ]),
                    ft.ListTile(leading=ft.Icon(ft.icons.PEOPLE), title=ft.Text("Manage Customers"), on_click=lambda _: page.go("/customers")),
                    ft.ListTile(leading=ft.Icon(ft.icons.HISTORY), title=ft.Text("Sales Logs"), on_click=lambda _: page.go("/history")),
                ], spacing=15, scroll="always"))
            ]))

        # ২. ইনভেন্টরি
        elif page.route == "/inventory":
            db.cursor.execute("SELECT * FROM products")
            prods = db.cursor.fetchall()
            lv = ft.ListView(expand=True, spacing=5)
            for p in prods:
                lv.controls.append(ft.ListTile(title=ft.Text(p[1]), subtitle=ft.Text(f"Price: {p[3]}"), trailing=ft.Text(f"{p[2]} Pcs")))
            page.views.append(ft.View("/inventory", [
                ft.AppBar(title=ft.Text("Inventory"), leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=go_back)),
                lv,
                ft.FloatingActionButton(icon=ft.icons.ADD, on_click=lambda _: page.go("/add_product"))
            ]))

        # ৩. নতুন প্রোডাক্ট
        elif page.route == "/add_product":
            name_in = ft.TextField(label="Name")
            price_in = ft.TextField(label="Price", keyboard_type="number")
            def save(e):
                if name_in.value:
                    db.cursor.execute("INSERT INTO products (name, stock, price) VALUES (?, ?, ?)", (name_in.value, 0, float(price_in.value or 0)))
                    db.conn.commit()
                    page.go("/")
            page.views.append(ft.View("/add_product", [
                ft.AppBar(title=ft.Text("Add Product"), leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=go_back)),
                ft.Container(padding=20, content=ft.Column([name_in, price_in, ft.ElevatedButton("Save", on_click=save, width=400)]))
            ]))

        # ৪. সেলস
        elif page.route == "/sales":
            db.cursor.execute("SELECT id, name, price, stock FROM products")
            items = db.cursor.fetchall()
            drop = ft.Dropdown(label="Item", options=[ft.dropdown.Option(key=str(i[0]), text=f"{i[1]} ({i[3]})") for i in items])
            qty = ft.TextField(label="Qty", value="1", keyboard_type="number")
            def sell(e):
                if not drop.value: return
                db.cursor.execute("SELECT name, price FROM products WHERE id=?", (drop.value,))
                res = db.cursor.fetchone()
                total = res[1] * int(qty.value or 1)
                db.cursor.execute("UPDATE products SET stock=stock-? WHERE id=?", (int(qty.value or 1), drop.value))
                db.cursor.execute("INSERT INTO sales_log (customer_name, product_name, qty, total, date) VALUES (?, ?, ?, ?, ?)",
                                 ("Walk-in", res[0], int(qty.value or 1), total, datetime.now().strftime("%Y-%m-%d %H:%M")))
                db.conn.commit()
                page.open(ft.AlertDialog(title=ft.Text("Success!"), content=ft.Text(f"Sale Done. Total: Tk {total}")))
                page.go("/")
            page.views.append(ft.View("/sales", [
                ft.AppBar(title=ft.Text("New Sale"), leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=go_back)),
                ft.Container(padding=20, content=ft.Column([drop, qty, ft.ElevatedButton("Confirm", on_click=sell, width=400, bgcolor="green", color="white")]))
            ]))

        # ৫. ইতিহাস
        elif page.route == "/history":
            db.cursor.execute("SELECT product_name, qty, total, date FROM sales_log ORDER BY id DESC")
            logs = db.cursor.fetchall()
            hlv = ft.ListView(expand=True)
            for l in logs:
                hlv.controls.append(ft.ListTile(title=ft.Text(f"{l[0]} x {l[1]}"), subtitle=ft.Text(l[3]), trailing=ft.Text(f"Tk {l[2]}")))
            page.views.append(ft.View("/history", [
                ft.AppBar(title=ft.Text("History"), leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=go_back)),
                hlv
            ]))

        page.update()

    page.on_route_change = route_change
    page.go("/")

ft.app(target=main)
