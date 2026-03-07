# scripts/create_admin.py
# Run from the project root: python scripts/create_admin.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db.database import SessionLocal
from src.db.repositories.admin_repository import AdminRepository
from src.core.security import hash_password


def main():
    print("=" * 40)
    print("Create Admin Account")
    print("=" * 40)

    email     = input("Email:      ").strip()
    password  = input("Password:   ").strip()
    full_name = input("Full name:  ").strip()

    if not email or not password or not full_name:
        print("ERROR: All fields are required.")
        return

    db   = SessionLocal()
    repo = AdminRepository(db)

    # Check duplicate
    if repo.get_by_email(email):
        print(f"\nERROR: An admin with email '{email}' already exists.")
        db.close()
        return

    admin = repo.create({
        "email":           email,
        "hashed_password": hash_password(password),
        "full_name":       full_name,
    })
    db.close()

    print(f"\nAdmin created successfully!")
    print(f"  ID:    {admin.id}")
    print(f"  Email: {admin.email}")
    print(f"  Name:  {admin.full_name}")


if __name__ == "__main__":
    main()