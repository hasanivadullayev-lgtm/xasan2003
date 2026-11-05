
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "ombor-pro-secret-key"
)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///omborxona.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


@app.context_processor
def inject_now():
    return {"now": datetime.now()}


# ==============================
# MAHSULOTLAR MODELI
# ==============================

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, default=0)
    min_stock = db.Column(db.Integer, default=5)
    price = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)


# ==============================
# KIRIM-CHIQIM MODELI
# ==============================

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(
        db.Integer,
        db.ForeignKey("product.id"),
        nullable=False
    )
    transaction_type = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    note = db.Column(db.String(250))
    created_at = db.Column(db.DateTime, default=datetime.now)

    product = db.relationship("Product", backref="transactions")


# ==============================
# BOSH SAHIFA
# ==============================

@app.route("/")
def dashboard():
    products = Product.query.all()

    total_products = len(products)
    total_quantity = sum(p.quantity for p in products)
    total_value = sum(p.quantity * p.price for p in products)

    low_stock = Product.query.filter(
        Product.quantity <= Product.min_stock
    ).all()

    recent_transactions = Transaction.query.order_by(
        Transaction.created_at.desc()
    ).limit(5).all()

    return render_template(
        "dashboard.html",
        total_products=total_products,
        total_quantity=total_quantity,
        total_value=total_value,
        low_stock=low_stock,
        recent_transactions=recent_transactions
    )


# ==============================
# MAHSULOTLAR RO'YXATI
# ==============================

@app.route("/products")
def products():
    search = request.args.get("search", "").strip()

    query = Product.query

    if search:
        query = query.filter(
            Product.name.ilike(f"%{search}%")
        )

    all_products = query.order_by(Product.id.desc()).all()

    return render_template(
        "products.html",
        products=all_products,
        search=search
    )


# ==============================
# MAHSULOT QO'SHISH
# ==============================

@app.route("/products/add", methods=["GET", "POST"])
def add_product():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        category = request.form.get("category", "").strip()

        try:
            quantity = int(request.form.get("quantity", 0))
            min_stock = int(request.form.get("min_stock", 5))
            price = float(request.form.get("price", 0))
        except (ValueError, TypeError):
            flash("Sonli qiymatlarni to'g'ri kiriting!", "danger")
            return redirect(url_for("add_product"))

        if not name or not category:
            flash("Barcha maydonlarni to'ldiring!", "danger")
            return redirect(url_for("add_product"))

        if quantity < 0 or min_stock < 0 or price < 0:
            flash("Manfiy qiymat kiritish mumkin emas!", "danger")
            return redirect(url_for("add_product"))

        product = Product(
            name=name,
            category=category,
            quantity=quantity,
            min_stock=min_stock,
            price=price
        )

        db.session.add(product)
        db.session.commit()

        flash("Mahsulot muvaffaqiyatli qo'shildi!", "success")

        return redirect(url_for("products"))

    return render_template(
        "product_form.html",
        product=None
    )


# ==============================
# MAHSULOTNI TAHRIRLASH
# ==============================

@app.route("/products/edit/<int:id>", methods=["GET", "POST"])
def edit_product(id):

    product = db.get_or_404(Product, id)

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        category = request.form.get("category", "").strip()

        try:
            quantity = int(request.form.get("quantity", 0))
            min_stock = int(request.form.get("min_stock", 5))
            price = float(request.form.get("price", 0))
        except (ValueError, TypeError):
            flash("Qiymatlarni to'g'ri kiriting!", "danger")
            return redirect(url_for("edit_product", id=id))

        if not name or not category:
            flash("Mahsulot nomi va kategoriyasini kiriting!", "danger")
            return redirect(url_for("edit_product", id=id))

        if quantity < 0 or min_stock < 0 or price < 0:
            flash("Manfiy qiymat kiritish mumkin emas!", "danger")
            return redirect(url_for("edit_product", id=id))

        product.name = name
        product.category = category
        product.quantity = quantity
        product.min_stock = min_stock
        product.price = price

        db.session.commit()

        flash("Mahsulot yangilandi!", "success")

        return redirect(url_for("products"))

    return render_template(
        "product_form.html",
        product=product
    )


# ==============================
# MAHSULOTNI O'CHIRISH
# ==============================

@app.route("/products/delete/<int:id>", methods=["POST"])
def delete_product(id):

    product = db.get_or_404(Product, id)

    if Transaction.query.filter_by(product_id=id).first():
        flash(
            "Bu mahsulotning kirim-chiqim tarixi mavjud. "
            "Tarixni saqlash uchun o'chirish mumkin emas!",
            "danger"
        )
        return redirect(url_for("products"))

    db.session.delete(product)
    db.session.commit()

    flash("Mahsulot o'chirildi!", "success")

    return redirect(url_for("products"))


# ==============================
# KIRIM-CHIQIM
# ==============================

@app.route("/transactions", methods=["GET", "POST"])
def transactions():

    if request.method == "POST":

        try:
            product_id = int(request.form.get("product_id"))
            quantity = int(request.form.get("quantity"))
        except (ValueError, TypeError):
            flash("Ma'lumotlarni to'g'ri kiriting!", "danger")
            return redirect(url_for("transactions"))

        transaction_type = request.form.get("transaction_type")
        note = request.form.get("note", "").strip()

        product = db.session.get(Product, product_id)

        if not product or quantity <= 0:
            flash("Mahsulot yoki miqdor noto'g'ri!", "danger")
            return redirect(url_for("transactions"))

        if transaction_type == "in":
            product.quantity += quantity

        elif transaction_type == "out":

            if product.quantity < quantity:
                flash(
                    "Omborda yetarli mahsulot mavjud emas!",
                    "danger"
                )
                return redirect(url_for("transactions"))

            product.quantity -= quantity

        else:
            flash("Operatsiya turini tanlang!", "danger")
            return redirect(url_for("transactions"))

        transaction = Transaction(
            product_id=product.id,
            transaction_type=transaction_type,
            quantity=quantity,
            note=note
        )

        db.session.add(transaction)
        db.session.commit()

        flash("Kirim-chiqim muvaffaqiyatli bajarildi!", "success")

        return redirect(url_for("transactions"))

    all_products = Product.query.order_by(Product.name).all()

    history = Transaction.query.order_by(
        Transaction.created_at.desc()
    ).all()

    return render_template(
        "transactions.html",
        products=all_products,
        transactions=history
    )


# ==============================
# HISOBOTLAR
# ==============================

@app.route("/reports")
def reports():

    products = Product.query.all()

    total_value = sum(
        p.quantity * p.price for p in products
    )

    total_in = db.session.query(
        db.func.sum(Transaction.quantity)
    ).filter_by(
        transaction_type="in"
    ).scalar() or 0

    total_out = db.session.query(
        db.func.sum(Transaction.quantity)
    ).filter_by(
        transaction_type="out"
    ).scalar() or 0

    return render_template(
        "reports.html",
        products=products,
        total_value=total_value,
        total_in=total_in,
        total_out=total_out
    )


# ==============================
# DATABASE VA SERVER
# ==============================

if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    print("OMBOR PRO SERVER ISHGA TUSHDI!")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    print("OMBOR PRO SERVER ISHGA TUSHDI!")

    app.run(
        host="127.0.0.1",
        port=8000,
        debug=False
    )