import flet as ft
import sqlite3
import os
from datetime import datetime
from fpdf import FPDF
from fpdf.enums import XPos, YPos

# --- ড্যাটাবেস ম্যানেজমেন্ট ---
class Database:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, stock INTEGER, price REAL)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS customers (id INTEGER PRIMARY KEY, name TEXT, phone TEXT)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS sales_log (id INTEGER PRIMARY KEY, customer_name TEXT, product_name TEXT, qty INTEGER, total REAL, date TEXT)")
        self.conn.commit()

# --- গ্লোবাল ভেরিয়েবল ---
# সেশন এরর এড়াতে আমরা সরাসরি ভেরিয়েবল ব্যবহার করব
working_directory = ""
app_db = None

# --- PDF ইনভয়েস জেনারেটর ---
def generate_pdf_invoice(customer, product, qty, price, total, save_dir):
    pdf = FPDF(unit="mm", format=(105, 148)) # A6 Size
    pdf.add_page()
    
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(0, 10, "Sayem FACTORY PRO", align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", size=9)
    pdf.cell(0, 5, "Sales Invoice / Money Receipt", align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)
    
    pdf.set_font("Helvetica", size=9)
    pdf.cell(0, 6, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 6, f"Customer: {customer}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 5, "-"*50, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_font("Helvetica", 'B', 9)
    pdf.cell(40, 8, "Product")
    pdf.cell(20, 8, "Qty")
    pdf.cell(25, 8, "Total", align='R', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_font("Helvetica", size=9)
    pdf.cell(40, 8, f"{product}")
    pdf.cell(20, 8, f"{qty}")
    pdf.cell(25, 8, f"{total}", align='R', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)
    
    pdf.set_font("Helvetica", 'B', 11)
    pdf.cell(0, 10, f"Grand Total: Tk {total}", border=1, align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.ln(5)
    pdf.set_font("Helvetica", 'I', 8)
    pdf.cell(0, 5, "Thank you for your business!", align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    file_name = f"invoice_{datetime.now().strftime('%H%M%S')}.pdf"
    full_path = os.path.join(save_dir, file_name)
    pdf.output(full_path)
    return file_name

def main(page: ft.Page):
    global working_directory, app_db
    
    # ১. অত্যন্ত শক্তিশালী পাথ ম্যানেজমেন্ট (সেশন ছাড়া)
    try:
        # অ্যান্ড্রয়েড APK এবং ডেস্কটপের জন্য সব ভার্সনে এটি কাজ করবে
        u_dir = getattr(page, "user_data_dir", None)
        
        if page.web:
            working_directory = os.path.join(os.getcwd(), "assets")
        elif u_dir:
            working_directory = u_dir
        else:
            working_directory = os.getcwd()

        if not os.path.exists(working_directory):
            os.makedirs(working_directory, exist_ok=True)
            
        # ডাটাবেস শুরু
        db_file = os.path.join(working_directory, "factory_pro_final.db")
        app_db = Database(db_file)
        
    except Exception as e:
        page.add(ft.Text(f"Fatal Startup Error: {e}", color="red"))
        return

    page.title = "Sayem Factory Pro"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 410
    page.window_height = 820
    page.padding = 0

    def go_back(e):
        if len(page.views) > 1:
            page.views.pop()
            top_view = page.views[-1]
            page.go(top_view.route)

    def route_change(e):
        if page.route == "/":
            page.views.clear()
            app_db.cursor.execute("SELECT name, stock FROM products")
            products_stock = app_db.cursor.fetchall()
            
            stock_chips = ft.GridView(expand=False, runs_count=2, max_extent=200, child_aspect_ratio=2.0, spacing=10, run_spacing=10)
            for ps in products_stock:
                color = ft.Colors.GREEN_400 if ps[1] > 20 else ft.Colors.RED_400
                stock_chips.controls.append(
                    ft.Container(padding=10, border_radius=12, bgcolor=ft.Colors.BLUE_GREY_50, border=ft.border.all(1, ft.Colors.BLUE_GREY_100),
                        content=ft.Column([ft.Text(ps[0], size=13, weight="bold", no_wrap=True), ft.Text(f"{ps[1]} Pcs", size=16, color=color, weight="bold")], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER))
                )

            page.views.append(ft.View("/", [
                ft.AppBar(title=ft.Text("UA Dashboard", weight="bold"), bgcolor=ft.Colors.BLUE_800, color=ft.Colors.WHITE, center_title=True),
                ft.Container(padding=20, content=ft.Column([
                    ft.Text("Live Stock Status", size=16, weight="bold", color=ft.Colors.BLUE_GREY_700),
                    stock_chips, ft.Divider(height=30),
                    ft.Row([
                        ft.ElevatedButton("Inventory", icon=ft.Icons.STORAGE, on_click=lambda _: page.go("/inventory"), expand=True, height=50),
                        ft.ElevatedButton("Sale", icon=ft.Icons.POINT_OF_SALE, on_click=lambda _: page.go("/sales"), expand=True, height=50, bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE),
                    ]),
                    ft.Card(content=ft.ListTile(leading=ft.Icon(ft.Icons.ADD_TASK, color=ft.Colors.BLUE), title=ft.Text("Add Production"), on_click=lambda _: page.go("/add_production"))),
                    ft.Card(content=ft.ListTile(leading=ft.Icon(ft.Icons.PEOPLE, color=ft.Colors.ORANGE), title=ft.Text("Customers"), on_click=lambda _: page.go("/customers"))),
                    ft.Card(content=ft.ListTile(leading=ft.Icon(ft.Icons.HISTORY, color=ft.Colors.BLUE_GREY), title=ft.Text("Sales Logs"), on_click=lambda _: page.go("/history"))),
                ], spacing=15, scroll=ft.ScrollMode.ALWAYS))
            ]))

        elif page.route == "/inventory":
            app_db.cursor.execute("SELECT * FROM products")
            prods = app_db.cursor.fetchall()
            lv = ft.ListView(expand=1, spacing=10, padding=20)
            for p in prods:
                lv.controls.append(ft.Container(padding=15, bgcolor=ft.Colors.BLUE_GREY_50, border_radius=10, content=ft.Row([ft.Column([ft.Text(p[1], weight="bold", size=16), ft.Text(f"Price: Tk {p[3]}", size=12)], expand=True), ft.Text(f"{p[2]} Pcs", weight="bold", color=ft.Colors.BLUE_700)])))
            page.views.append(ft.View("/inventory", [ft.AppBar(title=ft.Text("Stock Management"), leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=go_back)), lv, ft.FloatingActionButton(icon=ft.Icons.ADD, on_click=lambda _: page.go("/add_product_type"), bgcolor=ft.Colors.BLUE_700, foreground_color=ft.Colors.WHITE)]))

        elif page.route == "/add_product_type":
            name_in = ft.TextField(label="Product Name")
            price_in = ft.TextField(label="Selling Price", keyboard_type=ft.KeyboardType.NUMBER)
            def save_p(e):
                if name_in.value and price_in.value:
                    app_db.cursor.execute("INSERT INTO products (name, stock, price) VALUES (?, ?, ?)", (name_in.value, 0, float(price_in.value)))
                    app_db.conn.commit()
                    page.go("/")
            page.views.append(ft.View("/add_product_type", [ft.AppBar(title=ft.Text("New Product"), leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=go_back)), ft.Container(padding=30, content=ft.Column([name_in, price_in, ft.ElevatedButton("Save", on_click=save_p, width=400)]))]))

        elif page.route == "/add_production":
            app_db.cursor.execute("SELECT id, name FROM products")
            prods = app_db.cursor.fetchall()
            prod_drop = ft.Dropdown(label="Select Product", options=[ft.dropdown.Option(key=str(p[0]), text=p[1]) for p in prods])
            qty_in = ft.TextField(label="Qty Produced", keyboard_type=ft.KeyboardType.NUMBER)
            def update_prod(e):
                if prod_drop.value and qty_in.value:
                    app_db.cursor.execute("UPDATE products SET stock = stock + ? WHERE id = ?", (int(qty_in.value), int(prod_drop.value)))
                    app_db.conn.commit()
                    page.go("/")
            page.views.append(ft.View("/add_production", [ft.AppBar(title=ft.Text("Production"), leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=go_back)), ft.Container(padding=30, content=ft.Column([prod_drop, qty_in, ft.ElevatedButton("Update Stock", on_click=update_prod, width=400)]))]))

        elif page.route == "/sales":
            app_db.cursor.execute("SELECT name FROM customers")
            custs = app_db.cursor.fetchall()
            app_db.cursor.execute("SELECT id, name, price, stock FROM products")
            prods = app_db.cursor.fetchall()
            cust_drop = ft.Dropdown(label="Customer", options=[ft.dropdown.Option(text=c[0]) for c in custs])
            prod_drop = ft.Dropdown(label="Select Product", options=[ft.dropdown.Option(key=str(p[0]), text=f"{p[1]} (Stock: {p[3]})") for p in prods])
            qty_in = ft.TextField(label="Quantity", value="1")

            def make_invoice(e):
                if not prod_drop.value or not qty_in.value: return
                app_db.cursor.execute("SELECT name, price, stock FROM products WHERE id = ?", (prod_drop.value,))
                p_data = app_db.cursor.fetchone()
                if p_data[2] < int(qty_in.value):
                    page.open(ft.AlertDialog(title=ft.Text("Out of Stock!")))
                    return
                total = p_data[1] * int(qty_in.value)
                app_db.cursor.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (int(qty_in.value), int(prod_drop.value)))
                app_db.cursor.execute("INSERT INTO sales_log (customer_name, product_name, qty, total, date) VALUES (?, ?, ?, ?, ?)",
                                 (cust_drop.value or "Walk-in", p_data[0], int(qty_in.value), total, datetime.now().strftime("%Y-%m-%d %H:%M")))
                app_db.conn.commit()
                
                pdf_name = generate_pdf_invoice(cust_drop.value or "Walk-in", p_data[0], qty_in.value, p_data[1], total, working_directory)
                
                if page.web:
                    page.launch_url(f"/{pdf_name}")
                else:
                    page.launch_url(f"file://{os.path.join(working_directory, pdf_name)}")
                page.go("/")

            page.views.append(ft.View("/sales", [ft.AppBar(title=ft.Text("New Sale"), leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=go_back)), ft.Container(padding=30, content=ft.Column([cust_drop, prod_drop, qty_in, ft.ElevatedButton("Print Invoice", icon=ft.Icons.PRINT, on_click=make_invoice, width=400)]))]))

        elif page.route == "/customers":
            name_in = ft.TextField(label="Name")
            phone_in = ft.TextField(label="Phone")
            def save_c(e):
                if name_in.value:
                    app_db.cursor.execute("INSERT INTO customers (name, phone) VALUES (?, ?)", (name_in.value, phone_in.value))
                    app_db.conn.commit()
                    page.go("/")
            page.views.append(ft.View("/customers", [ft.AppBar(title=ft.Text("Manage Customers"), leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=go_back)), ft.Container(padding=30, content=ft.Column([name_in, phone_in, ft.ElevatedButton("Save", on_click=save_c)]))]))

        elif page.route == "/history":
            app_db.cursor.execute("SELECT id, customer_name, product_name, qty, total, date FROM sales_log ORDER BY id DESC")
            history = app_db.cursor.fetchall()
            h_list = ft.ListView(expand=True, spacing=10, padding=20)
            for h in history:
                def reprint_invoice(e, customer=h[1], product=h[2], qty=h[3], total=h[4]):
                    price = total / qty if qty > 0 else 0
                    pdf_name = generate_pdf_invoice(customer, product, qty, price, total, working_directory)
                    if page.web:
                        page.launch_url(f"/{pdf_name}")
                    else:
                        page.launch_url(f"file://{os.path.join(working_directory, pdf_name)}")
                    snack = ft.SnackBar(ft.Text(f"Invoice generated for {customer}"))
                    page.overlay.append(snack)
                    snack.open = True
                    page.update()

                h_list.controls.append(ft.Card(content=ft.ListTile(leading=ft.Icon(ft.Icons.PRINT, color=ft.Colors.BLUE_GREY_400), title=ft.Text(f"{h[2]} x {h[3]}", weight="bold"), subtitle=ft.Text(f"Client: {h[1]} | Date: {h[5]}"), trailing=ft.Text(f"Tk {h[4]}", weight="bold", color=ft.Colors.BLUE_800), on_click=reprint_invoice)))
            page.views.append(ft.View("/history", [ft.AppBar(title=ft.Text("Sales History", weight="bold"), leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=go_back), bgcolor=ft.Colors.BLUE_GREY_100), h_list]))

        page.update()

    page.on_route_change = route_change
    page.on_view_pop = go_back
    page.go(page.route)

ft.app(target=main, assets_dir="assets")
