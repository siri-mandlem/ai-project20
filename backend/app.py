import os

from flask import Flask, jsonify, render_template
from sqlalchemy import inspect, text

from .config import Config
from .models import db
from .routes import api, ensure_demo_data


FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
app = Flask(__name__, template_folder=FRONTEND_DIR, static_folder=FRONTEND_DIR, static_url_path="/static")
app.config.from_object(Config)
db.init_app(app)
app.register_blueprint(api)


def migrate_legacy_schema():
    """Add columns introduced after the first generated Neon schema."""
    inspector = inspect(db.engine)
    additions = {
        "users": {
            "username": "VARCHAR(100) NOT NULL DEFAULT 'Customer'",
            "password_hash": "VARCHAR(255)",
        },
        "products": {
            "stock": "INTEGER NOT NULL DEFAULT 25",
            "featured": "BOOLEAN NOT NULL DEFAULT FALSE",
        },
        "orders": {
            "customer_name": "VARCHAR(160) NOT NULL DEFAULT 'Demo Shopper'",
            "shipping_address": "TEXT NOT NULL DEFAULT ''",
            "created_at": "TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP",
        },
    }
    for table, columns in additions.items():
        existing = {column["name"] for column in inspector.get_columns(table)}
        for column, definition in columns.items():
            if column not in existing:
                db.session.execute(text(f'ALTER TABLE "{table}" ADD COLUMN "{column}" {definition}'))
    db.session.commit()


@app.get("/")
@app.get("/<page>")
def frontend(page="index"):
    allowed = {"index", "home", "products", "search", "product-detail", "cart", "checkout", "order-history"}
    if page not in allowed:
        return jsonify({"message": "Page not found."}), 404
    return render_template("index.html")


with app.app_context():
    db.create_all()
    migrate_legacy_schema()
    ensure_demo_data()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
