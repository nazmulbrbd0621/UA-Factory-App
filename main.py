import flet as ft
import sqlite3
import os
from datetime import datetime

# --- ডাটাবেস ক্লাস (পুরোপুরি নিরাপদ) ---
class Database:
    def __init__(self, db_path):
        try:
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self.cursor = self.conn.cursor()
            self.cursor.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, stock INTEGER, price REAL)")
            self.cursor.execute("CREATE TABLE IF NOT EXISTS customers (id INTEGER PRIMARY KEY, name TEXT, phone TEXT)")
            self.cursor.execute("CREATE TABLE IF NOT EXISTS sales_log (id INTEGER PRIMARY KEY, customer_name TEXT, product_name TEXT, qty INTEGER, total REAL, date TEXT)")
            self.conn.commit()
        except Exception as e:
            raise Exception(f"Database Error: {str(e)}")

def main(page: ft.Page):
    page.title = "UA Factory Pro"
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # এরর বা সাকসেস মেসেজ দেখার জন্য
    debug_text = ft.Text(size=12, color="blue")
    
    # ১. অ্যান্ড্রয়েড-সেফ পাথ লজিক
    try:
        # Flet-এর এই প্রপার্টিটি অ্যান্ড্রয়েড APK-তে অটোমেটিক একটি রাইটেবল পাথ দেয়
        db_dir = page.user_data_dir 
        if not db_dir:
            db_dir = os.getcwd() # পিসিতে চালানোর জন্য

        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            
        db_file_path = os.path.join(db_dir, "factory_final.db")
        db = Database(db_file_path)
        debug_text.value = f"Success! Path: {db_dir}"
    except Exception as e:
        page.add(ft.Text(f"FATAL PATH ERROR: {str(e)}", color="red", weight="bold", size=18))
        page.update()
        return

    # ২. নেভিগেশন লজিক
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
            
            stock_grid = ft.GridView(expand=False, runs_count=2, child_aspect_ratio=2.2, spacing=10)
            for ps in products_stock:
                color = ft.Colors.GREEN_400 if ps[1] > 15 else ft.Colors.RED_400
                stock_grid.controls.append(
                    ft.Container(padding=10, border_radius=10, bgcolor=ft.Colors.BLUE_GREY_50,
                        content=ft.Column([
                            ft.Text(ps[0], size=12, weight="bold", no_wrap=True),
                            ft.Text(f"{ps[1]} Pcs", size=15, color=color, weight="bold")
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER))
                )

            page.views.append(
                ft.View("/", [
                    ft.AppBar(title=ft.Text("UA Factory Dashboard"), bgcolor=ft.Colors.BLUE_800, color="white"),
                    ft.Container(padding=15, content=ft.Column([
                        debug_text, # সফল হলে পাথ দেখাবে
                        ft.Text("Live Stock Status", size=18, weight="bold"),
                        stock_grid,
                        ft.Divider(),
                        ft.Row([
                            ft.ElevatedButton("Inventory", icon=ft.Icons.STORAGE, on_click=lambda _: page.go("/inventory"), expand=True),
                            ft.ElevatedButton("New Sale", icon=ft.Icons.SHOPPING_CART, on_click=lambda _: page.go("/sales"), expand=True, bgcolor=ft.Colors.GREEN_700, color="white"),
                        ]),
                        ft.Card(content=ft.ListTile(leading=ft.Icon(ft.Icons.PEOPLE), title=ft.Text("Customers"), on_click=lambda _: page.go("/customers"))),
                        ft.Card(content=ft.ListTile(leading=ft.Icon(ft.Icons.HISTORY), title=ft.Text("Sales Logs"), on_click=lambda _: page.go("/history"))),
                    ], spacing=10, scroll=ft.ScrollMode.ALWAYS))
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
                ft.AppBar(title=ft.Text("Inventory"), leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=go_back)),
                lv,
                ft.FloatingActionButton(icon=ft.Icons.ADD, on_click=lambda _: page.go("/add_product"))
            ]))

        # --- নতুন প্রোডাক্ট অ্যাড ---
        elif page.route == "/add_product":
            name_in = ft.TextField(label="Product Name")
            price_in = ft.TextField(label="Unit Price", keyboard_type=ft.KeyboardType.NUMBER)
            def save_p(e):
                if name_in.value:
                    db.cursor.execute("INSERT INTO products (name, stock, price) VALUES (?, ?, ?)", (name_in.value, 0, float(price_in.value or 0)))
                    db.conn.commit()
                    page.go("/")
            page.views.append(ft.View("/add_product", [
                ft.AppBar(title=ft.Text("Add Product"), leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=go_back)),
                ft.Container(padding=20, content=ft.Column([name_in, price_in, ft.ElevatedButton("Save", on_click=save_p, width=400)]))
            ]))

        # --- সেলস পেজ ---
        elif page.route == "/sales":
            db.cursor.execute("SELECT id, name, price, stock FROM products")
            prods = db.cursor.fetchall()
            prod_drop = ft.Dropdown(label="Select Item", options=[ft.dropdown.Option(key=str(p[0]), text=f"{p[1]} (Stock:{p[3]})") for p in prods])
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
                page.open(ft.AlertDialog(title=ft.Text("Sale Success!"), content=ft.Text(f"Total: Tk {total}")))
                page.go("/")

            page.views.append(ft.View("/sales", [
                ft.AppBar(title=ft.Text("New Sale"), leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=go_back)),
                ft.Container(padding=20, content=ft.Column([prod_drop, qty_in, ft.ElevatedButton("Complete Sale", on_click=make_sale, bgcolor=ft.Colors.GREEN_700, color="white", width=400)]))
            ]))

        page.update()

    page.on_route_change = route_change
    page.go("/")

ft.app(target=main)
