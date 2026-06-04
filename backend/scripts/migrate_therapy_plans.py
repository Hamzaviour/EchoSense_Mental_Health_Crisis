import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.extensions import db
import app.models  # noqa: F401


def migrate():
    app = create_app()
    with app.app_context():
        db.create_all()
        print("Therapy plans table ready (db.create_all).")


if __name__ == "__main__":
    migrate()
