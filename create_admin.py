from getpass import getpass

from database.connection import SessionLocal
from models.admin import Admin
from core.security import hash_password


db = SessionLocal()

try:
    username = input("Enter admin username: ").strip()
    email = input("Enter admin email: ").strip().lower()

    password = getpass("Enter admin password: ")
    confirm_password = getpass("Confirm admin password: ")

    if not username or not email or not password:
        raise ValueError("All fields are required.")

    if password != confirm_password:
        raise ValueError("Passwords do not match.")

    existing_admin = db.query(Admin).filter(
        (Admin.username == username) |
        (Admin.email == email)
    ).first()

    if existing_admin:
        raise ValueError("An admin with this username or email already exists.")

    new_admin = Admin(
        username=username,
        email=email,
        hashed_password=hash_password(password),
    )

    db.add(new_admin)
    db.commit()

    print("Admin account created successfully!")

except Exception as error:
    db.rollback()
    print(f"Error: {error}")

finally:
    db.close()