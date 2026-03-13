import flet as ft
import sqlite3
import os
from datetime import datetime

# --- ড্যাটাবেস ম্যানেজমেন্ট (Android Safe) ---
class Database:
    def __init__(self, db_path):
        try:
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self.cursor = self.conn.cursor()
            self.create_tables()
        except Exception as e:
            raise Exception(f"Database Connect Error: {str(e)}")

    def create_tables(self):
        self.cursor.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, stock INTEGER, price REAL)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS customers (id INTEGER PRIMARY KEY, name TEXT, phone TEXT)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS sales_log (id INTEGER PRIMARY KEY, customer_name TEXT, product_name TEXT, qty INTEGER, total REAL, date TEXT)")
        self.conn.commit()

def main(page: ft.Page):
    page.title = "Sayem Factory Pro"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 10
    
    # এরর হ্যান্ডলিংয়ের জন্য মেইন কন্টেইনার
    main_container = ft.Column(scroll=ft.ScrollMode.ALWAYS, expand=True)

    # ১. অ্যান্ড্রয়েড এবং পিসির জন্য ১০০% নিরাপদ পাথ লজিক
    try:
        # অ্যান্ড্রয়েডে লেখার জন্য এই পাথটি সবচেয়ে স্ট্যাবল
        if os.name == 'nt': # পিসির জন্য
            working_dir = os.getcwd()
        else: # অ্যান্ড্রয়েডের জন্য
            working_dir = os.path.expanduser("~") 

        db_file = os.path.join(working_dir, "factory_pro_v100.db")
        db = Database(db_file)
    except Exception as e:
        # যদি শুরুতেই এরর হয়, তবে স্ক্রিনে দেখাবে
        page.add(ft.Text(f"CRITICAL STARTUP ERROR: {str(e)}", color="red", size=20, weight="bold"))
        page.update()
        return

    def go_back(e):
        if len(page.views) > 1:
            page.views.pop()
            page.go(page.views[-1].route)

    def route_change(e):
        page.views.clear()
        
        # --- হোম ড্যাশবোর্ড ---
        if page.route == "/":
            db.cursor.execute("SELECT name, stock FROM products")
            products_stock = db.cursor.fetchall()
            
            stock_grid = ft.GridView(expand=False, runs_count=2, child_aspect_ratio=2.0, spacing=10)
            for ps in products_stock:
                color = ft.colors.GREEN_400 if ps[1] > 10 else ft.colors.RED_400
                stock_grid.controls.append(
                    ft.Container(padding=10, border_radius=10, bgcolor=ft.colors.BLUE_GREY_50,
                        content=ft.Column([
                            ft.Text(ps[0], size=12, weight="bold", no_wrap=True),
                            ft.Text(f"{ps[1]} Pcs", size=15, color=color, weight="bold")
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER))
                )

            page.views.append(
                ft.View("/", [
                    ft.AppBar(title=ft.Text("Sayem Factory Dashboard"), bgcolor=ft.colors.BLUE_800, color=ft.colors.WHITE),
                    ft.Container(padding=10, content=ft.Column([
                        ft.Text("Live Stock Status", size=18, weight="bold"),
                        stock_grid,
                        ft.Divider(),
                        ft.Row([
                            ft.ElevatedButton("Stock", icon=ft.icons.INVENTORY, on_click=lambda _: page.go("/inventory"), expand=True),
                            ft.ElevatedButton("New Sale", icon=ft.icons.SHOPPING_CART, on_click=lambda _: page.go("/sales"), expand=True, bgcolor=ft.colors.GREEN_700, color=ft.colors.WHITE),
                        ]),
                        ft.ListTile(leading=ft.Icon(ft.icons.PEOPLE), title=ft.Text("Customers"), on_click=lambda _: page.go("/customers")),
                        ft.ListTile(leading=ft.Icon(ft.icons.HISTORY), title=ft.Text("Sales Logs"), on_click=lambda _: page.go("/history")),
                    ], spacing=15))
                ])
            )

        # --- ইনভেন্টরি পেজ ---
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

        # --- নতুন প্রোডাক্ট যোগ করা ---
        elif page.route == "/add_product":
            name_in = ft.TextField(label="Product Name")
            price_in = ft.TextField(label="Price", keyboard_type=ft.KeyboardType.NUMBER)
            def save_p(e):
                if name_in.value:
                    db.cursor.execute("INSERT INTO products (name, stock, price) VALUES (?, ?, ?)", (name_in.value, 0, float(price_in.value or 0)))
                    db.conn.commit()
                    page.go("/")
            page.views.append(ft.View("/add_product", [
                ft.AppBar(title=ft.Text("Add Product"), leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=go_back)),
                ft.Container(padding=20, content=ft.Column([name_in, price_in, ft.ElevatedButton("Save", on_click=save_p)]))
            ]))

        # --- সেলস পেজ (PDF ছাড়া সহজ ভার্সন) ---
        elif page.route == "/sales":
            db.cursor.execute("SELECT id, name, price, stock FROM products")
            prods = db.cursor.fetchall()
            prod_drop = ft.Dropdown(label="Select Product", options=[ft.dropdown.Option(key=str(p[0]), text=f"{p[1]} ({p[3]})") for p in prods])
            qty_in = ft.TextField(label="Quantity", value="1", keyboard_type=ft.KeyboardType.NUMBER)

            def make_sale(e):
                if not prod_drop.value: return
                db.cursor.execute("SELECT name, price FROM products WHERE id = ?", (prod_drop.value,))
                p_data = db.cursor.fetchone()
                total = p_data[1] * int(qty_in.value or 1)
                
                db.cursor.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (int(qty_in.value or 1), prod_drop.value))
                db.cursor.execute("INSERT INTO sales_log (customer_name, product_name, qty, total, date) VALUES (?, ?, ?, ?, ?)",
                                 ("Walk-in", p_data[0], int(qty_in.value or 1), total, datetime.now().strftime("%Y-%m-%d %H:%M")))
                db.conn.commit()
                
                # পিডিএফের বদলে এখন শুধু মেসেজ দেখাবে (টেস্টিংয়ের জন্য)
                page.open(ft.AlertDialog(title=ft.Text("Sale Confirmed!"), content=ft.Text(f"Total: Tk {total}\nStock Updated.")))
                page.go("/")

            page.views.append(ft.View("/sales", [
                ft.AppBar(title=ft.Text("New Sale"), leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=go_back)),
                ft.Container(padding=20, content=ft.Column([prod_drop, qty_in, ft.ElevatedButton("Confirm Sale", on_click=make_sale, bgcolor=ft.colors.GREEN_700, color=ft.colors.WHITE)]))
            ]))

        # --- ইতিহাস পেজ ---
        elif page.route == "/history":
            db.cursor.execute("SELECT id, customer_name, product_name, qty, total, date FROM sales_log ORDER BY id DESC")
            history = db.cursor.fetchall()
            hlv = ft.ListView(expand=True)
            for h in history:
                hlv.controls.append(ft.ListTile(title=ft.Text(f"{h[2]} x {h[3]}"), subtitle=ft.Text(f"{h[5]}"), trailing=ft.Text(f"Tk {h[4]}")))
            page.views.append(ft.View("/history", [
                ft.AppBar(title=ft.Text("History"), leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=go_back)),
                hlv
            ]))

        page.update()

    page.on_route_change = route_change
    page.go("/")

ft.app(target=main)
