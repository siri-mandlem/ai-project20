import os


def database_url():
    value = os.getenv("DATABASE_URL", "sqlite:///store.db")
    if value.startswith("postgres://"):
        value = value.replace("postgres://", "postgresql+psycopg2://", 1)
    elif value.startswith("postgresql://"):
        value = value.replace("postgresql://", "postgresql+psycopg2://", 1)
    return value


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
    SQLALCHEMY_DATABASE_URI = database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False
