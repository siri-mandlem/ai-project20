import os

from flask import Flask, jsonify, render_template

from .config import Config
from .models import db
from .routes import api, ensure_demo_data


FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
app = Flask(__name__, template_folder=FRONTEND_DIR, static_folder=FRONTEND_DIR, static_url_path="/static")
app.config.from_object(Config)
db.init_app(app)
app.register_blueprint(api)


@app.get("/")
@app.get("/<page>")
def frontend(page="index"):
    allowed = {"index", "home", "products", "search", "product-detail", "cart", "checkout", "order-history"}
    if page not in allowed:
        return jsonify({"message": "Page not found."}), 404
    return render_template("index.html")


with app.app_context():
    db.create_all()
    ensure_demo_data()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
