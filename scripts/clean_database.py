# scripts/clean_database.py
# Run from project root: python scripts/clean_database.py
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from src.db.database import SessionLocal
from src.core.config import settings


def main():
    db = SessionLocal()

    kept = db.execute(text("SELECT email FROM users WHERE role = 'super_admin'")).fetchall()
    if not kept:
        print("ABORT: no super_admin user found — refusing to wipe (you'd lock yourself out).")
        db.close()
        return

    print(f"Keeping super_admin(s): {[r[0] for r in kept]}")
    confirm = input("This deletes ALL organizations, users (non-super_admin), students, courses, sessions, and attendance. Type 'yes' to continue: ")
    if confirm.strip().lower() != "yes":
        print("Cancelled.")
        db.close()
        return

    # Order respects FK dependencies: attendance -> students/course_sessions -> courses -> users/organizations
    db.execute(text("DELETE FROM attendance"))
    db.execute(text("DELETE FROM students"))
    db.execute(text("DELETE FROM course_sessions"))
    db.execute(text("DELETE FROM courses"))
    db.execute(text("DELETE FROM users WHERE role != 'super_admin'"))
    db.execute(text("DELETE FROM organizations"))

    # Reset auto-increment sequences so reseeded IDs start clean.
    for table in ["students", "courses", "course_sessions", "attendance", "organizations"]:
        db.execute(text(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), 1, false)"))
    db.execute(text(
        "SELECT setval(pg_get_serial_sequence('users', 'id'), COALESCE((SELECT MAX(id) FROM users), 1), true)"
    ))

    db.commit()
    db.close()

    # FAISS embeddings are keyed to student_id — stale entries would misattribute
    # recognitions after reseeding, so wipe the index files too.
    for path in [settings.FAISS_INDEX_PATH, settings.FAISS_ID_MAP_PATH]:
        if os.path.exists(path):
            os.remove(path)
            print(f"Removed {path}")

    print("Database cleaned. Only the super_admin user remains.")


if __name__ == "__main__":
    main()