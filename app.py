from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")
DB_PATH = os.path.join(os.path.dirname(__file__), "train_catering.db")

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'customer'
        );
        CREATE TABLE IF NOT EXISTS foods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            available INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            train_number TEXT NOT NULL,
            pnr TEXT NOT NULL,
            coach_seat TEXT NOT NULL,
            station TEXT NOT NULL,
            delivery_time TEXT NOT NULL,
            total REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Received',
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            food_id INTEGER NOT NULL,
            food_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            FOREIGN KEY(order_id) REFERENCES orders(id),
            FOREIGN KEY(food_id) REFERENCES foods(id)
        );
        """)
        count = con.execute("SELECT COUNT(*) FROM foods").fetchone()[0]
        if count == 0:
            foods = [
                ("Veg Meals", "Rice, chapati, dal, vegetables and curd", "Meals", 120),
                ("Paneer Biryani", "Aromatic rice with paneer and spices", "Meals", 150),
                ("Veg Sandwich", "Fresh vegetable sandwich", "Snacks", 60),
                ("Idli (3 pcs)", "Steamed idlis with chutney", "Breakfast", 50),
                ("Masala Dosa", "Crispy dosa with potato masala", "Breakfast", 80),
                ("Tea", "Hot Indian tea", "Beverages", 15),
                ("Coffee", "Fresh filter coffee", "Beverages", 25),
                ("Fruit Bowl", "Seasonal cut fruits", "Snacks", 70)
            ]
            con.executemany("INSERT INTO foods(name,description,category,price) VALUES(?,?,?,?)", foods)
        admin = con.execute("SELECT id FROM users WHERE email=?", ("admin@trainmeal.demo",)).fetchone()
        if not admin:
            con.execute("INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)",
                        ("Administrator","admin@trainmeal.demo",generate_password_hash("Admin@123"),"admin"))

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Administrator access required.", "danger")
            return redirect(url_for("index"))
        return fn(*args, **kwargs)
    return wrapper

@app.route("/")
def index():
    with db() as con:
        foods = con.execute("SELECT * FROM foods WHERE available=1 ORDER BY category,name").fetchall()
    return render_template("index.html", foods=foods)

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        name=request.form.get("name","").strip()
        email=request.form.get("email","").strip().lower()
        password=request.form.get("password","")
        if not name or not email or len(password)<6:
            flash("Enter all details. Password must contain at least 6 characters.", "danger")
        else:
            try:
                with db() as con:
                    con.execute("INSERT INTO users(name,email,password) VALUES(?,?,?)",
                                (name,email,generate_password_hash(password)))
                flash("Account created. Please log in.", "success")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                flash("That email is already registered.", "danger")
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        email=request.form.get("email","").strip().lower()
        password=request.form.get("password","")
        with db() as con:
            user=con.execute("SELECT * FROM users WHERE email=?",(email,)).fetchone()
        if user and check_password_hash(user["password"],password):
            session.clear()
            session["user_id"]=user["id"]; session["name"]=user["name"]; session["role"]=user["role"]
            return redirect(url_for("admin") if user["role"]=="admin" else url_for("index"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))

@app.route("/add-to-cart/<int:food_id>", methods=["POST"])
def add_to_cart(food_id):
    with db() as con:
        food=con.execute("SELECT * FROM foods WHERE id=? AND available=1",(food_id,)).fetchone()
    if not food:
        flash("Food item is unavailable.", "danger")
    else:
        cart=session.get("cart",{})
        key=str(food_id)
        cart[key]=min(int(cart.get(key,0))+1,20)
        session["cart"]=cart
        flash(food["name"]+" added to cart.", "success")
    return redirect(request.referrer or url_for("index"))

@app.route("/cart")
def cart():
    cart_data=[]; total=0
    cart_items=session.get("cart",{})
    if cart_items:
        ids=[int(x) for x in cart_items]
        marks=",".join("?" for _ in ids)
        with db() as con:
            foods=con.execute(f"SELECT * FROM foods WHERE id IN ({marks}) AND available=1",ids).fetchall()
        for food in foods:
            qty=int(cart_items.get(str(food["id"]),0))
            subtotal=food["price"]*qty; total+=subtotal
            cart_data.append({"food":food,"qty":qty,"subtotal":subtotal})
    return render_template("cart.html", items=cart_data,total=total)

@app.route("/update-cart", methods=["POST"])
def update_cart():
    cart=session.get("cart",{})
    for key in list(cart):
        try: qty=int(request.form.get(key,0))
        except ValueError: qty=0
        if qty<=0: cart.pop(key,None)
        else: cart[key]=min(qty,20)
    session["cart"]=cart
    return redirect(url_for("cart"))

@app.route("/checkout", methods=["GET","POST"])
@login_required
def checkout():
    cart_items=session.get("cart",{})
    if not cart_items:
        flash("Your cart is empty.", "warning"); return redirect(url_for("index"))
    if request.method=="POST":
        fields={k:request.form.get(k,"").strip() for k in ["train_number","pnr","coach_seat","station","delivery_time"]}
        if not all(fields.values()):
            flash("Please complete all journey and delivery details.", "danger")
        else:
            ids=[int(x) for x in cart_items]
            marks=",".join("?" for _ in ids)
            with db() as con:
                foods=con.execute(f"SELECT * FROM foods WHERE id IN ({marks}) AND available=1",ids).fetchall()
                total=sum(f["price"]*int(cart_items.get(str(f["id"]),0)) for f in foods)
                if not foods or total<=0:
                    flash("Your cart has no available items.", "danger"); return redirect(url_for("cart"))
                cur=con.execute("""INSERT INTO orders(user_id,train_number,pnr,coach_seat,station,delivery_time,total,created_at)
                    VALUES(?,?,?,?,?,?,?,?)""",
                    (session["user_id"],fields["train_number"],fields["pnr"],fields["coach_seat"],
                     fields["station"],fields["delivery_time"],total,datetime.now().strftime("%d-%m-%Y %H:%M")))
                order_id=cur.lastrowid
                for f in foods:
                    qty=int(cart_items.get(str(f["id"]),0))
                    if qty>0:
                        con.execute("INSERT INTO order_items(order_id,food_id,food_name,quantity,unit_price) VALUES(?,?,?,?,?)",
                                    (order_id,f["id"],f["name"],qty,f["price"]))
            session["cart"]={}
            flash(f"Order #{order_id} placed successfully! Payment is marked as Cash on Delivery for this demo.", "success")
            return redirect(url_for("my_orders"))
    return render_template("checkout.html")

@app.route("/my-orders")
@login_required
def my_orders():
    with db() as con:
        orders=con.execute("SELECT * FROM orders WHERE user_id=? ORDER BY id DESC",(session["user_id"],)).fetchall()
        items={}
        for order in orders:
            items[order["id"]]=con.execute("SELECT * FROM order_items WHERE order_id=?",(order["id"],)).fetchall()
    return render_template("my_orders.html",orders=orders,items=items)

@app.route("/admin")
@login_required
@admin_required
def admin():
    with db() as con:
        orders=con.execute("""SELECT orders.*,users.name,users.email FROM orders
            JOIN users ON users.id=orders.user_id ORDER BY orders.id DESC""").fetchall()
        foods=con.execute("SELECT * FROM foods ORDER BY category,name").fetchall()
        items={}
        for order in orders:
            items[order["id"]]=con.execute("SELECT * FROM order_items WHERE order_id=?",(order["id"],)).fetchall()
    return render_template("admin.html",orders=orders,foods=foods,items=items)

@app.route("/admin/food", methods=["POST"])
@login_required
@admin_required
def add_food():
    name=request.form.get("name","").strip()
    category=request.form.get("category","").strip()
    description=request.form.get("description","").strip()
    try: price=float(request.form.get("price","0"))
    except ValueError: price=0
    if name and category and 0<price<10000:
        with db() as con:
            con.execute("INSERT INTO foods(name,description,category,price) VALUES(?,?,?,?)",
                        (name,description,category,price))
        flash("Food item added.", "success")
    else: flash("Enter a name, category and valid price.", "danger")
    return redirect(url_for("admin"))

@app.route("/admin/food/<int:food_id>/toggle", methods=["POST"])
@login_required
@admin_required
def toggle_food(food_id):
    with db() as con:
        con.execute("UPDATE foods SET available=CASE available WHEN 1 THEN 0 ELSE 1 END WHERE id=?",(food_id,))
    return redirect(url_for("admin"))

@app.route("/admin/order/<int:order_id>", methods=["POST"])
@login_required
@admin_required
def update_order(order_id):
    status=request.form.get("status","")
    if status in ["Received","Preparing","Out for delivery","Delivered","Cancelled"]:
        with db() as con:
            con.execute("UPDATE orders SET status=? WHERE id=?",(status,order_id))
    flash("Order status updated.", "success")
    return redirect(url_for("admin"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
