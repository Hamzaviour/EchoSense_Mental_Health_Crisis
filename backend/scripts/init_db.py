"""Initialize database tables and seed data."""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.extensions import db
import app.models  # noqa: F401


def init():
    app = create_app()
    with app.app_context():
        db.create_all()
        print("Database tables created.")
    from scripts.seed_assessments import seed
    seed()


if __name__ == "__main__":
    init()
