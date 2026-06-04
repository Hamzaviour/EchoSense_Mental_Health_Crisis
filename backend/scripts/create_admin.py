"""Create default admin and counselor demo users."""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.extensions import db
from app.models import Counselor, User
from app.models.user import UserRole
from app.utils.helpers import generate_counselor_id, hash_password

DEMO_COUNSELOR = {
    "email": "counselor@echo.local",
    "password": "counselor123",
    "full_name": "Dr. Sarah Counselor",
}
DEMO_ADMIN = {
    "email": "admin@echo.local",
    "password": "admin123",
    "full_name": "System Admin",
}


def create_demo_users():
    app = create_app()
    with app.app_context():
        for demo, role, extra in [
            (DEMO_COUNSELOR, UserRole.COUNSELOR, "counselor"),
            (DEMO_ADMIN, UserRole.ADMIN, None),
        ]:
            if User.query.filter_by(email=demo["email"]).first():
                print(f"Exists: {demo['email']}")
                continue
            user = User(
                email=demo["email"],
                password_hash=hash_password(demo["password"]),
                role=role,
            )
            db.session.add(user)
            db.session.flush()
            if extra == "counselor":
                db.session.add(Counselor(
                    user_id=user.id,
                    counselor_id=generate_counselor_id(),
                    full_name=demo["full_name"],
                    specialization="Crisis Intervention",
                ))
            print(f"Created {demo['email']} / {demo['password']}")
        db.session.commit()


if __name__ == "__main__":
    create_demo_users()
