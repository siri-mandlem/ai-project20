import os
import sys

import pytest


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from backend.app import app  # noqa: E402


@pytest.fixture()
def client():
    app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI="sqlite:///:memory:")
    with app.app_context():
        from backend.models import db
        db.drop_all()
        db.create_all()
        from backend.routes import ensure_demo_data
        ensure_demo_data()
    return app.test_client()


def test_products_and_cart_flow(client):
    products = client.get("/api/products")
    assert products.status_code == 200
    product_id = products.get_json()[0]["id"]
    cart = client.post("/api/cart", json={"product_id": product_id, "quantity": 2})
    assert cart.status_code == 201
    assert cart.get_json()["count"] == 2


def test_checkout_creates_order(client):
    product_id = client.get("/api/products").get_json()[0]["id"]
    client.post("/api/cart", json={"product_id": product_id})
    response = client.post("/api/orders", json={"customer_name": "Test Shopper", "shipping_address": "1 Test Street"})
    assert response.status_code == 201
    assert response.get_json()["status"] == "placed"
