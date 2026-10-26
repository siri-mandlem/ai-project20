# Northstar Goods

A small full-stack e-commerce demo generated for the requested shopping flow.

## Features

- Home page with featured products
- Product search and category filtering
- Product detail pages
- Add to cart, quantity changes, and removal
- Checkout and persisted order history
- PostgreSQL/Neon support through `DATABASE_URL`
- Render deployment configuration in `render.yaml`

## Run locally

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r backend/requirements.txt
python -m backend.app
```

The app uses SQLite automatically when `DATABASE_URL` is not set. Open http://localhost:5000.

## Neon + Render deployment

1. Create a Neon PostgreSQL database and copy its pooled connection string.
2. Push this project directory to a GitHub repository.
3. Create a Render Web Service from that repository.
4. Render will use `render.yaml`, install `backend/requirements.txt`, and start `gunicorn backend.app:app`.
5. Set `DATABASE_URL` to the Neon connection string. Set `SECRET_KEY` to a long random value.

The Flask app creates the tables and seeds the catalog on startup. The SQL schema is also available at `database/schema.sql` for manual Neon setup.
