import flet as ft
import sqlite3
import os
from datetime import datetime
from fpdf import FPDF
from fpdf.enums import XPos, YPos

# --- ড্যাটাবেস সেটআপ ---
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


# --- PDF ইনভয়েস জেনারেটর (Deprecation Warnings Fixed) ---
def generate_pdf_invoice(customer, product, qty, price, total, save_path):
    pdf = FPDF(unit="mm", format=(105, 148))
    pdf.add_page()
    
    # Header
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(0, 10, "Sayem FACTORY PRO", align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", size=9)
    pdf.cell(0, 5, "Sales Invoice / Money Receipt", align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)
    
    # Info
    pdf.set_font("Helvetica", size=9)
    pdf.cell(0, 6, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 6, f"Customer: {customer}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 5, "-"*50, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    # Content Table
    pdf.set_font("Helvetica", 'B', 9)
    pdf.cell(40, 8, "Product")
    pdf.cell(20, 8, "Qty")
    pdf.cell(25, 8, "Total", align='R', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_font("Helvetica", size=9)
    pdf.cell(40, 8, f"{product}")
    pdf.cell(20, 8, f"{qty}")
    pdf.cell(25, 8, f"{total}", align='R', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)
    
    # Grand Total
    pdf.set_font("Helvetica", 'B', 11)
    pdf.cell(0, 10, f"Grand Total: Tk {total}", border=1, align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.ln(5)
    pdf.set_font("Helvetica", 'I', 8)
    pdf.cell(0, 5, "Thank you for your business!", align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # ফাইলের নাম ও পাথ ফিক্সড করা
    file_name = f"invoice_{datetime.now().strftime('%H%M%S')}.pdf"
    full_path = os.path.join(save_path, file_name)
    pdf.output(full_path)
    return full_path

def main(page: ft.Page):
    # ১. ডাটাবেস পাথ নির্ধারণ (Web mode ফিক্সড)
    # getattr ব্যবহার করা হয়েছে যাতে user_data_dir না থাকলে এরর না দেয়
    user_data_path = getattr(page, "user_data_dir", None)
    
    if user_data_path is None:
        # যদি ওয়েব মোড বা Ngrok হয়, তবে বর্তমান ফোল্ডার ব্যবহার করবে
        user_data_path = os.getcwd()
    
    # ফোল্ডার নিশ্চিত করা
    if not os.path.exists(user_data_path):
        try:
            os.makedirs(user_data_path)
        except:
            pass

    # ডাটাবেস ফাইল তৈরি
    db_file = os.path.join(user_data_path, "factory_pro.db")
    db = Database(db_file)

    # ২. PDF সেভ করার জন্য পাবলিক পাথ (Download Folder)
    # ফোনের জন্য ডাউনলোড ফোল্ডার, পিসির জন্য বর্তমান ফোল্ডার
    if page.platform == ft.PagePlatform.ANDROID:
        pdf_save_path = "/storage/emulated/0/Download"
        if not os.path.exists(pdf_save_path):
            pdf_save_path = user_data_path
    else:
        pdf_save_path = os.getcwd()

    # সেশন স্টোরেজে পাথটি সেভ রাখা যাতে পরে পাওয়া যায়
    page.session.set("pdf_path", pdf_save_path)

    # বাকি সেটিংস
    page.title = "Sayem Factory Pro"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 410
    page.window_height = 820
    page.padding = 0
    
    # ... আপনার বাকি কোড ...
    def go_back(e):
        if len(page.views) > 1:
            page.views.pop()
            top_view = page.views[-1]
            page.go(top_view.route)

    # --- রাউট চেঞ্জ লজিক ---
    def route_change(e):
        # হোম পেজ হলে ভিউ ক্লিয়ার হবে, সাব পেজ হলে স্ট্যাকে অ্যাড হবে
        if page.route == "/":
            page.views.clear()
            
            db.cursor.execute("SELECT name, stock FROM products")
            products_stock = db.cursor.fetchall()
            
            # --- ১. গ্রিড ভিউ সিস্টেম ---
            stock_chips = ft.GridView(
                expand=False,
                runs_count=2, # ২ কলামের গ্রিড
                max_extent=200,
                child_aspect_ratio=2.0,
                spacing=10,
                run_spacing=10,
            )
            for ps in products_stock:
                color = ft.Colors.GREEN_400 if ps[1] > 20 else ft.Colors.RED_400
                stock_chips.controls.append(
                    ft.Container(
                        padding=10, border_radius=12, bgcolor=ft.Colors.BLUE_GREY_50,
                        border=ft.border.all(1, ft.Colors.BLUE_GREY_100),
                        content=ft.Column([
                            ft.Text(ps[0], size=13, weight="bold", no_wrap=True),
                            ft.Text(f"{ps[1]} Pcs", size=16, color=color, weight="bold")
                        ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    )
                )

            page.views.append(
                ft.View(
                    "/",
                    [
                        ft.AppBar(title=ft.Text("Production Dashboard", weight="bold"), bgcolor=ft.Colors.BLUE_800, color=ft.Colors.WHITE, center_title=True),
                        ft.Container(
                            padding=20,
                            content=ft.Column([
                                ft.Text("Live Inventory Status", size=16, weight="bold", color=ft.Colors.BLUE_GREY_700),
                                stock_chips,
                                ft.Divider(height=30),
                                ft.Row([
                                    ft.ElevatedButton("Stock", icon=ft.Icons.STORAGE, on_click=lambda _: page.go("/inventory"), expand=True, height=50),
                                    ft.ElevatedButton("Sale", icon=ft.Icons.POINT_OF_SALE, on_click=lambda _: page.go("/sales"), expand=True, height=50, bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE),
                                ]),
                                ft.Card(content=ft.ListTile(leading=ft.Icon(ft.Icons.ADD_TASK, color=ft.Colors.BLUE), title=ft.Text("Add Production"), on_click=lambda _: page.go("/add_production"))),
                                ft.Card(content=ft.ListTile(leading=ft.Icon(ft.Icons.PEOPLE, color=ft.Colors.ORANGE), title=ft.Text("Customers"), on_click=lambda _: page.go("/customers"))),
                                ft.Card(content=ft.ListTile(leading=ft.Icon(ft.Icons.HISTORY, color=ft.Colors.BLUE_GREY), title=ft.Text("Sales Logs"), on_click=lambda _: page.go("/history"))),
                            ], spacing=15, scroll=ft.ScrollMode.ALWAYS)
                        ),
                    ]
                )
            )

        # --- ২. ইনভেন্টরি পেজ ---
        elif page.route == "/inventory":
            db.cursor.execute("SELECT * FROM products")
            products = db.cursor.fetchall()
            list_view = ft.ListView(expand=1, spacing=10, padding=20)
            for p in products:
                list_view.controls.append(
                    ft.Container(
                        padding=15, bgcolor=ft.Colors.BLUE_GREY_50, border_radius=10,
                        content=ft.Row([
                            ft.Column([ft.Text(p[1], weight="bold", size=16), ft.Text(f"Price: Tk {p[3]}", size=12)], expand=True),
                            ft.Text(f"{p[2]} Pcs", weight="bold", color=ft.Colors.BLUE_700)
                        ])
                    )
                )
            page.views.append(
                ft.View("/inventory", [
                    ft.AppBar(title=ft.Text("Stock Management"), leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=go_back)),
                    list_view,
                    ft.FloatingActionButton(icon=ft.Icons.ADD, on_click=lambda _: page.go("/add_product_type"), bgcolor=ft.Colors.BLUE_700, foreground_color=ft.Colors.WHITE)
                ])
            )

        # --- ৩. নতুন প্রোডাক্ট টাইপ যোগ করা ---
        elif page.route == "/add_product_type":
            name_in = ft.TextField(label="Product Name")
            price_in = ft.TextField(label="Selling Price", keyboard_type=ft.KeyboardType.NUMBER)
            def save_p(e):
                if name_in.value and price_in.value:
                    db.cursor.execute("INSERT INTO products (name, stock, price) VALUES (?, ?, ?)", (name_in.value, 0, float(price_in.value)))
                    db.conn.commit()
                    page.go("/") # সরাসরি হোমে ফিরে রিফ্রেশ করা
            page.views.append(ft.View("/add_product_type", [
                ft.AppBar(title=ft.Text("New Product"), leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=go_back)),
                ft.Container(padding=30, content=ft.Column([name_in, price_in, ft.ElevatedButton("Save", on_click=save_p, width=400)]))
            ]))

        # --- ৪. উৎপাদন এন্ট্রি ---
        elif page.route == "/add_production":
            db.cursor.execute("SELECT id, name FROM products")
            prods = db.cursor.fetchall()
            prod_drop = ft.Dropdown(label="Select Product", options=[ft.dropdown.Option(key=str(p[0]), text=p[1]) for p in prods])
            qty_in = ft.TextField(label="Qty Produced", keyboard_type=ft.KeyboardType.NUMBER)
            def update_prod(e):
                if prod_drop.value and qty_in.value:
                    db.cursor.execute("UPDATE products SET stock = stock + ? WHERE id = ?", (int(qty_in.value), int(prod_drop.value)))
                    db.conn.commit()
                    page.go("/")
            page.views.append(ft.View("/add_production", [
                ft.AppBar(title=ft.Text("Production"), leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=go_back)),
                ft.Container(padding=30, content=ft.Column([prod_drop, qty_in, ft.ElevatedButton("Update Stock", on_click=update_prod, width=400)]))
            ]))

        # --- ৫. সেলস ও ইনভয়েস ---
        elif page.route == "/sales":
            db.cursor.execute("SELECT name FROM customers")
            custs = db.cursor.fetchall()
            db.cursor.execute("SELECT id, name, price, stock FROM products")
            prods = db.cursor.fetchall()
            cust_drop = ft.Dropdown(label="Customer", options=[ft.dropdown.Option(text=c[0]) for c in custs])
            prod_drop = ft.Dropdown(label="Product", options=[ft.dropdown.Option(key=str(p[0]), text=f"{p[1]} (Stock: {p[3]})") for p in prods])
            qty_in = ft.TextField(label="Quantity", value="1")

            def make_invoice(e):
                if not prod_drop.value or not qty_in.value: return
                db.cursor.execute("SELECT name, price, stock FROM products WHERE id = ?", (prod_drop.value,))
                p_data = db.cursor.fetchone()
                if p_data[2] < int(qty_in.value):
                    page.open(ft.AlertDialog(title=ft.Text("Out of Stock!")))
                    return
                total = p_data[1] * int(qty_in.value)
                db.cursor.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (int(qty_in.value), int(prod_drop.value)))
                db.cursor.execute("INSERT INTO sales_log (customer_name, product_name, qty, total, date) VALUES (?, ?, ?, ?, ?)",
                                 (cust_drop.value or "Walk-in", p_data[0], int(qty_in.value), total, datetime.now().strftime("%Y-%m-%d %H:%M")))
                db.conn.commit()
                
                # save_path হিসেবে user_data_path যোগ করা হয়েছে
                pdf_file = generate_pdf_invoice(
                    cust_drop.value or "Walk-in", 
                    p_data[0], 
                    qty_in.value, 
                    p_data[1], 
                    total, 
                    user_data_path # এই প্যারামিটারটি যোগ করুন
                )
                page.launch_url(f"file://{pdf_file}")
                page.go("/")

            page.views.append(ft.View("/sales", [
                ft.AppBar(title=ft.Text("New Sale"), leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=go_back)),
                ft.Container(padding=30, content=ft.Column([cust_drop, prod_drop, qty_in, ft.ElevatedButton("Print Invoice", icon=ft.Icons.PRINT, on_click=make_invoice, width=400)]))
            ]))

        # --- কাস্টমার ও ইতিহাস ---
        elif page.route == "/customers":
            name_in = ft.TextField(label="Name")
            phone_in = ft.TextField(label="Phone")
            def save_c(e):
                if name_in.value:
                    db.cursor.execute("INSERT INTO customers (name, phone) VALUES (?, ?)", (name_in.value, phone_in.value))
                    db.conn.commit()
                    page.go("/")
            page.views.append(ft.View("/customers", [
                ft.AppBar(title=ft.Text("Manage Customers"), leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=go_back)),
                ft.Container(padding=30, content=ft.Column([name_in, phone_in, ft.ElevatedButton("Save", on_click=save_c)]))
            ]))

        # --- ইতিহাস (History) সেকশন ---
        elif page.route == "/history":
            db.cursor.execute("SELECT id, customer_name, product_name, qty, total, date FROM sales_log ORDER BY id DESC")
            history = db.cursor.fetchall()
            
            # নিশ্চিত করুন h_list লুপের আগে ডিফাইন করা আছে এবং expand=True দেওয়া আছে
            h_list = ft.ListView(expand=True, spacing=10, padding=20)
            
            for h in history:
                # পাইথন ক্লোজার ফিক্স: ডিফল্ট আর্গুমেন্ট দিয়ে ডাটা ক্যাপচার করা হয়েছে
                def reprint_invoice(e, customer=h[1], product=h[2], qty=h[3], total=h[4]):
                    price = total / qty if qty > 0 else 0
                    
                    # save_path হিসেবে user_data_path যোগ করা হয়েছে
                    pdf_file = generate_pdf_invoice(
                        customer, 
                        product, 
                        qty, 
                        price, 
                        total, 
                        user_data_path # এই প্যারামিটারটি যোগ করুন
                    )
                    
                    # এটি অ্যান্ড্রয়েড এবং পিসি উভয়ের জন্য সবচেয়ে স্ট্যাবল
                    try:
                        if page.platform == ft.PagePlatform.ANDROID:
                            # ফোনে সেভ হওয়ার পর নোটিফিকেশন দেওয়া
                            snack_bar = ft.SnackBar(ft.Text(f"PDF saved in Downloads folder!"))
                            page.overlay.append(snack_bar)
                            snack_bar.open = True
                        
                        page.launch_url(f"file://{pdf_file}")
                    except Exception as e:
                        print(f"Error launching PDF: {e}")
                    
                    # ইউজারকে জানানো
                    # নতুন পদ্ধতি
                    snack_bar = ft.SnackBar(ft.Text(f"Re-printing invoice for {customer}..."))
                    page.overlay.append(snack_bar)
                    snack_bar.open = True
                    page.update()

                h_list.controls.append(
                    ft.Card(
                        content=ft.ListTile(
                            leading=ft.Icon(ft.Icons.PRINT, color=ft.Colors.BLUE_GREY_400),
                            title=ft.Text(f"{h[2]} x {h[3]}", weight="bold"),
                            subtitle=ft.Text(f"Client: {h[1]} | Date: {h[5]}"),
                            trailing=ft.Text(f"Tk {h[4]}", weight="bold", color=ft.Colors.BLUE_800),
                            on_click=reprint_invoice # এখানে টাচ করলে রি-প্রিন্ট হবে
                        )
                    )
                )
            
            page.views.append(
                ft.View(
                    "/history",
                    [
                        ft.AppBar(
                            title=ft.Text("Sales History", weight="bold"),
                            leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=go_back),
                            bgcolor=ft.Colors.BLUE_GREY_100
                        ),
                        h_list # আপনার লিস্ট ভিউ
                    ]
                )
            )
        page.update()

    page.on_route_change = route_change
    page.on_view_pop = go_back
    page.go(page.route)

ft.app(target=main)
