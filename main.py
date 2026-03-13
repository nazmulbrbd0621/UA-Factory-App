import flet as ft
import sqlite3
import os
from datetime import datetime
from fpdf import FPDF
from fpdf.enums import XPos, YPos

# --- ড্যাটাবেস সেটআপ (নিরাপদ পাথ) ---
class Database:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, stock INTEGER, price REAL)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS customers (id INTEGER PRIMARY KEY, name TEXT, phone TEXT)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS sales_log (id INTEGER PRIMARY KEY, customer_name TEXT, product_name TEXT, qty INTEGER, total REAL, date TEXT)")
        self.conn.commit()

# --- PDF ইনভয়েস জেনারেটর ---
def generate_pdf_invoice(customer, product, qty, total, save_dir):
    pdf = FPDF(unit="mm", format=(105, 148))
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(0, 10, "UA FACTORY PRO", align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", size=9)
    pdf.cell(0, 5, "Sales Invoice / Money Receipt", align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)
    pdf.set_font("Helvetica", size=9)
    pdf.cell(0, 6, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 6, f"Customer: {customer}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 5, "-"*50, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", 'B', 9)
    pdf.cell(40, 8, f"{product} x {qty}")
    pdf.cell(20, 8, f"Tk {total}", align='R', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)
    pdf.set_font("Helvetica", 'B', 11)
    pdf.cell(0, 10, f"Grand Total: Tk {total}", border=1, align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    file_name = f"invoice_{datetime.now().strftime('%H%M%S')}.pdf"
    full_path = os.path.join(save_dir, file_name)
    pdf.output(full_path)
    return full_path

def main(page: ft.Page):
    # ১. অত্যন্ত শক্তিশালী পাথ ম্যানেজমেন্ট
    try:
        if os.name == 'nt':
            working_dir = os.path.join(os.getcwd(), "assets")
        else:
            working_dir = os.path.expanduser("~") 

        if not os.path.exists(working_dir):
            os.makedirs(working_dir, exist_ok=True)
            
        db_file = os.path.join(working_dir, "factory_pro_final.db")
        db = Database(db_file)
    except Exception as e:
        page.add(ft.Text(f"Fatal Startup Error: {e}", color="red"))
        return

    page.title = "UA Factory Pro"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 410
    page.window_height = 820

    def go_back(e):
        if len(page.views) > 1:
            page.views.pop()
            page.go(page.views[-1].route)

    def route_change(e):
        if page.route == "/":
            page.views.clear()
            db.cursor.execute("SELECT name, stock FROM products")
            products_stock = db.cursor.fetchall()
            
            # ড্যাশবোর্ড গ্রিড ভিউ
            stock_grid = ft.GridView(expand=False, runs_count=2, child_aspect_ratio=2.0, spacing=10)
            for ps in products_stock:
                color = ft.colors.GREEN_400 if ps[1] > 20 else ft.colors.RED_400
                stock_grid.controls.append(
                    ft.Container(padding=10, border_radius=12, bgcolor=ft.colors.BLUE_GREY_50,
                        content=ft.Column([
                            ft.Text(ps[0], size=13, weight="bold", no_wrap=True),
                            ft.Text(f"{ps[1]} Pcs", size=16, color=color, weight="bold")
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER))
                )

            page.views.append(ft.View("/", [
                ft.AppBar(title=ft.Text("UA Dashboard", weight="bold"), bgcolor=ft.colors.BLUE_800, color="white", center_title=True),
                ft.Container(padding=20, content=ft.Column([
                    ft.Text("Live Stock Status", size=16, weight="bold"),
                    stock_grid, ft.Divider(height=30),
                    ft.Row([
                        ft.ElevatedButton("Stock", icon=ft.icons.STORAGE, on_click=lambda _: page.go("/inventory"), expand=True, height=50),
                        ft.ElevatedButton("Sale", icon=ft.icons.POINT_OF_SALE, on_click=lambda _: page.go("/sales"), expand=True, height=50, bgcolor=ft.colors.GREEN_600, color="white"),
                    ]),
                    ft.Card(content=ft.ListTile(leading=ft.Icon(ft.icons.ADD_TASK, color="blue"), title=ft.Text("Add Production"), on_click=lambda _: page.go("/add_production"))),
                    ft.Card(content=ft.ListTile(leading=ft.Icon(ft.icons.PEOPLE, color="orange"), title=ft.Text("Manage Customers"), on_click=lambda _: page.go("/customers"))),
                    ft.Card(content=ft.ListTile(leading=ft.Icon(ft.icons.HISTORY, color="grey"), title=ft.Text("Sales Logs"), on_click=lambda _: page.go("/history"))),
                ], spacing=15, scroll=ft.ScrollMode.ALWAYS))
            ]))

        elif page.route == "/inventory":
            db.cursor.execute("SELECT * FROM products")
            prods = db.cursor.fetchall()
            lv = ft.ListView(expand=True, spacing=10, padding=20)
            for p in prods:
                lv.controls.append(ft.Container(padding=15, bgcolor=ft.colors.BLUE_GREY_50, border_radius=10, content=ft.Row([ft.Column([ft.Text(p[1], weight="bold", size=16), ft.Text(f"Price: Tk {p[3]}", size=12)], expand=True), ft.Text(f"{p[2]} Pcs", weight="bold", color=ft.colors.BLUE_700)])))
            page.views.append(ft.View("/inventory", [ft.AppBar(title=ft.Text("Stock Management"), leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=go_back)), lv, ft.FloatingActionButton(icon=ft.icons.ADD, on_click=lambda _: page.go("/add_product_type"))]))

        elif page.route == "/add_product_type":
            name_in = ft.TextField(label="Product Name")
            price_in = ft.TextField(label="Selling Price", keyboard_type=ft.KeyboardType.NUMBER)
            def save_p(e):
                if name_in.value:
                    db.cursor.execute("INSERT INTO products (name, stock, price) VALUES (?, ?, ?)", (name_in.value, 0, float(price_in.value or 0)))
                    db.conn.commit()
                    page.go("/")
            page.views.append(ft.View("/add_product_type", [ft.AppBar(title=ft.Text("New Product"), leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=go_back)), ft.Container(padding=30, content=ft.Column([name_in, price_in, ft.ElevatedButton("Save", on_click=save_p, width=400)]))]))

        elif page.route == "/add_production":
            db.cursor.execute("SELECT id, name FROM products")
            prods = db.cursor.fetchall()
            prod_drop = ft.Dropdown(label="Select Product", options=[ft.dropdown.Option(key=str(p[0]), text=p[1]) for p in prods])
            qty_in = ft.TextField(label="Qty Produced Today", keyboard_type=ft.KeyboardType.NUMBER)
            def update_prod(e):
                if prod_drop.value:
                    db.cursor.execute("UPDATE products SET stock = stock + ? WHERE id = ?", (int(qty_in.value or 0), int(prod_drop.value)))
                    db.conn.commit()
                    page.go("/")
            page.views.append(ft.View("/add_production", [ft.AppBar(title=ft.Text("Production Entry"), leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=go_back)), ft.Container(padding=30, content=ft.Column([prod_drop, qty_in, ft.ElevatedButton("Update Stock", on_click=update_prod, width=400)]))]))

        elif page.route == "/sales":
            db.cursor.execute("SELECT name FROM customers")
            custs = db.cursor.fetchall()
            db.cursor.execute("SELECT id, name, price, stock FROM products")
            prods = db.cursor.fetchall()
            cust_drop = ft.Dropdown(label="Customer", options=[ft.dropdown.Option(text=c[0]) for c in custs])
            prod_drop = ft.Dropdown(label="Select Product", options=[ft.dropdown.Option(key=str(p[0]), text=f"{p[1]} ({p[3]})") for p in prods])
            qty_in = ft.TextField(label="Quantity", value="1")
            def make_invoice(e):
                if not prod_drop.value: return
                db.cursor.execute("SELECT name, price FROM products WHERE id = ?", (prod_drop.value,))
                p_data = db.cursor.fetchone()
                total = p_data[1] * int(qty_in.value or 1)
                db.cursor.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (int(qty_in.value or 1), int(prod_drop.value)))
                db.cursor.execute("INSERT INTO sales_log (customer_name, product_name, qty, total, date) VALUES (?, ?, ?, ?, ?)", (cust_drop.value or "Walk-in", p_data[0], int(qty_in.value or 1), total, datetime.now().strftime("%Y-%m-%d %H:%M")))
                db.conn.commit()
                pdf_file = generate_pdf_invoice(cust_drop.value or "Walk-in", p_data[0], qty_in.value, total, working_dir)
                page.launch_url(f"file://{pdf_file}")
                page.go("/")
            page.views.append(ft.View("/sales", [ft.AppBar(title=ft.Text("New Sale"), leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=go_back)), ft.Container(padding=30, content=ft.Column([cust_drop, prod_drop, qty_in, ft.ElevatedButton("Print Invoice", icon=ft.icons.PRINT, on_click=make_invoice, width=400)]))]))

        elif page.route == "/customers":
            name_in = ft.TextField(label="Name")
            phone_in = ft.TextField(label="Phone")
            def save_c(e):
                if name_in.value:
                    db.cursor.execute("INSERT INTO customers (name, phone) VALUES (?, ?)", (name_in.value, phone_in.value))
                    db.conn.commit()
                    page.go("/")
            page.views.append(ft.View("/customers", [ft.AppBar(title=ft.Text("Customers"), leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=go_back)), ft.Container(padding=30, content=ft.Column([name_in, phone_in, ft.ElevatedButton("Save", on_click=save_c)]))]))

        elif page.route == "/history":
            db.cursor.execute("SELECT id, customer_name, product_name, qty, total, date FROM sales_log ORDER BY id DESC")
            history = db.cursor.fetchall()
            h_list = ft.ListView(expand=True, spacing=10, padding=20)
            for h in history:
                def reprint(e, c=h[1], p=h[2], q=h[3], t=h[4]):
                    pdf = generate_pdf_invoice(c, p, q, t, working_dir)
                    page.launch_url(f"file://{pdf}")
                    page.snack_bar = ft.SnackBar(ft.Text("Re-printing slip..."))
                    page.snack_bar.open = True
                    page.update()
                h_list.controls.append(ft.Card(content=ft.ListTile(leading=ft.Icon(ft.icons.PRINT), title=ft.Text(f"{h[2]} x {h[3]}"), subtitle=ft.Text(f"{h[1]} | {h[5]}"), trailing=ft.Text(f"Tk {h[4]}"), on_click=reprint)))
            page.views.append(ft.View("/history", [ft.AppBar(title=ft.Text("Sales History"), leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=go_back)), h_list]))

        page.update()

    page.on_route_change = route_change
    page.go("/")

ft.app(target=main)
