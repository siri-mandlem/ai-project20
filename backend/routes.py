from decimal import Decimal

from flask import Blueprint, jsonify, request
from sqlalchemy import or_

from .models import CartItem, Order, OrderItem, Product, User, db


api = Blueprint("api", __name__, url_prefix="/api")
DEMO_USER_ID = 1


def money(value):
    return float(Decimal(value or 0).quantize(Decimal("0.01")))


def product_json(product):
    return {"id": product.id, "name": product.name, "description": product.description, "category": product.category, "price": money(product.price), "image_url": product.image_url, "stock": product.stock, "featured": product.featured}


def cart_json():
    items = CartItem.query.filter_by(user_id=DEMO_USER_ID).all()
    result, total, count = [], Decimal("0"), 0
    for item in items:
        line_total = Decimal(item.product.price) * item.quantity
        total += line_total
        count += item.quantity
        result.append({"id": item.id, "quantity": item.quantity, "product": product_json(item.product), "line_total": money(line_total)})
    return {"items": result, "total": money(total), "count": count}


@api.get("/health")
def health():
    return jsonify({"status": "ok"})


@api.get("/categories")
def categories():
    values = db.session.query(Product.category).distinct().order_by(Product.category).all()
    return jsonify([value[0] for value in values])


@api.get("/products")
def products():
    query = Product.query
    search, category = request.args.get("q", "").strip(), request.args.get("category", "").strip()
    if search:
        query = query.filter(or_(Product.name.ilike(f"%{search}%"), Product.description.ilike(f"%{search}%")))
    if category:
        query = query.filter_by(category=category)
    if request.args.get("featured") == "true":
        query = query.filter_by(featured=True)
    return jsonify([product_json(product) for product in query.order_by(Product.featured.desc(), Product.id).all()])


@api.get("/products/<int:product_id>")
def product_detail(product_id):
    return jsonify(product_json(db.get_or_404(Product, product_id)))


@api.get("/cart")
def get_cart():
    return jsonify(cart_json())


@api.post("/cart")
def add_to_cart():
    data = request.get_json(silent=True) or {}
    product = db.session.get(Product, data.get("product_id"))
    if not product:
        return jsonify({"message": "Product not found."}), 404
    quantity = max(1, int(data.get("quantity", 1)))
    item = CartItem.query.filter_by(user_id=DEMO_USER_ID, product_id=product.id).first()
    if item:
        item.quantity = min(item.quantity + quantity, product.stock)
    else:
        db.session.add(CartItem(user_id=DEMO_USER_ID, product_id=product.id, quantity=min(quantity, product.stock)))
    db.session.commit()
    return jsonify(cart_json()), 201


@api.patch("/cart/<int:product_id>")
def update_cart(product_id):
    item = CartItem.query.filter_by(user_id=DEMO_USER_ID, product_id=product_id).first()
    if not item:
        return jsonify({"message": "Cart item not found."}), 404
    quantity = int((request.get_json(silent=True) or {}).get("quantity", 1))
    if quantity <= 0:
        db.session.delete(item)
    else:
        item.quantity = min(quantity, item.product.stock)
    db.session.commit()
    return jsonify(cart_json())


@api.delete("/cart/<int:product_id>")
def remove_from_cart(product_id):
    item = CartItem.query.filter_by(user_id=DEMO_USER_ID, product_id=product_id).first()
    if item:
        db.session.delete(item)
        db.session.commit()
    return jsonify(cart_json())


def order_json(order):
    return {"id": order.id, "status": order.status, "total_price": money(order.total_price), "customer_name": order.customer_name, "shipping_address": order.shipping_address, "created_at": order.created_at.isoformat(), "items": [{"product_name": item.product_name, "quantity": item.quantity, "unit_price": money(item.unit_price)} for item in order.items]}


@api.post("/orders")
def checkout():
    data = request.get_json(silent=True) or {}
    name, address = str(data.get("customer_name", "")).strip(), str(data.get("shipping_address", "")).strip()
    cart = CartItem.query.filter_by(user_id=DEMO_USER_ID).all()
    if not cart:
        return jsonify({"message": "Your cart is empty."}), 400
    if not name or not address:
        return jsonify({"message": "Customer name and shipping address are required."}), 400
    total = sum((Decimal(item.product.price) * item.quantity for item in cart), Decimal("0"))
    order = Order(user_id=DEMO_USER_ID, total_price=total, customer_name=name, shipping_address=address)
    db.session.add(order)
    for item in cart:
        db.session.add(OrderItem(order=order, product_id=item.product_id, product_name=item.product.name, quantity=item.quantity, unit_price=item.product.price))
        item.product.stock = max(0, item.product.stock - item.quantity)
        db.session.delete(item)
    db.session.commit()
    return jsonify(order_json(order)), 201


@api.get("/orders")
def order_history():
    orders = Order.query.filter_by(user_id=DEMO_USER_ID).order_by(Order.created_at.desc()).all()
    return jsonify([order_json(order) for order in orders])


def ensure_demo_data():
    if not db.session.get(User, DEMO_USER_ID):
        db.session.add(User(id=DEMO_USER_ID, username="Demo Shopper", email="demo@buildflow.local", role="customer"))
    if Product.query.count() == 0:
        db.session.add_all([
            Product(name="Aurora Headphones", description="Immersive wireless sound with all-day comfort.", category="Tech", price=129.99, image_url="https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=900&q=80", stock=18, featured=True),
            Product(name="Orbit Smartwatch", description="A minimal health and productivity companion.", category="Tech", price=179.00, image_url="https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=900&q=80", stock=12, featured=True),
            Product(name="Cloud Knit Sweater", description="Soft recycled yarn, relaxed fit, everyday warmth.", category="Fashion", price=74.50, image_url="https://images.unsplash.com/photo-1610652492500-ded49ceeb378?auto=format&fit=crop&w=900&q=80", stock=24, featured=True),
            Product(name="Studio Backpack", description="A structured carryall for work, travel, and creativity.", category="Lifestyle", price=89.00, image_url="https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=900&q=80", stock=15),
            Product(name="Ceramic Pour Over", description="Slow mornings made better with a beautiful brew kit.", category="Home", price=42.00, image_url="https://images.unsplash.com/photo-1517256064527-09c73fc73e38?auto=format&fit=crop&w=900&q=80", stock=30),
            Product(name="Desk Light Mini", description="Warm, focused light for late-night ideas.", category="Home", price=58.00, image_url="https://images.unsplash.com/photo-1507473885765-e6ed057f782c?auto=format&fit=crop&w=900&q=80", stock=20),
        ])
    db.session.commit()
