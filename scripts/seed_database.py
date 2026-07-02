# scripts/seed_database.py
# Run from project root: python scripts/seed_database.py
# Requires: pip install Faker (not in requirements.txt)
import sys
import os
import random
from datetime import date, datetime, time, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
from faker import Faker
from sqlalchemy.orm import Session

from src.db.database import SessionLocal
from src.core.security import hash_password
from src.core.config import settings
from src.models.organization import Organization
from src.models.user import User
from src.models.student import Student
from src.models.course import Course
from src.models.course_session import CourseSession
from src.models.attendance import Attendance
from src.ai.recognition_pipeline import RecognitionPipeline
from src.ai.detector import FaceNotDetectedException, MultipleFacesException

fake = Faker()

ARABIC_MALE_FIRST_NAMES = [
    "Ahmed", "Mohamed", "Mahmoud", "Youssef", "Omar", "Khaled", "Karim", "Amr",
    "Tarek", "Hassan", "Hussein", "Ali", "Mostafa", "Ibrahim", "Sherif",
    "Ayman", "Waleed", "Sameh", "Adel", "Hesham",
]
ARABIC_FEMALE_FIRST_NAMES = [
    "Fatima", "Aisha", "Mariam", "Nour", "Sara", "Yasmin", "Salma", "Heba",
    "Dina", "Rania", "Mona", "Hoda", "Rana", "Nada", "Amira",
    "Laila", "Rasha", "Shaimaa", "Ghada", "Mai",
]
ARABIC_LAST_NAMES = [
    "El-Sayed", "Abdel Rahman", "Hassan", "Ibrahim", "Mostafa", "El-Shazly",
    "Farouk", "Kamal", "Naguib", "Mansour", "Saad", "Abdallah", "Fathy",
    "Gaber", "Zaki", "Rashad", "Tawfik", "Salem", "Attia", "Younes",
]
_used_names: set[str] = set()

def _unique_arabic_name(first_names: list[str]) -> str:
    for _ in range(200):
        candidate = f"{random.choice(first_names)} {random.choice(ARABIC_LAST_NAMES)}"
        if candidate not in _used_names:
            _used_names.add(candidate)
            return candidate
    candidate = f"{random.choice(first_names)} {random.choice(ARABIC_LAST_NAMES)} {random.randint(1, 999)}"
    _used_names.add(candidate)
    return candidate

def arabic_name_male() -> str:
    return _unique_arabic_name(ARABIC_MALE_FIRST_NAMES)

def arabic_name_female() -> str:
    return _unique_arabic_name(ARABIC_FEMALE_FIRST_NAMES)


DUMMY_FACES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dummy_faces")
ATTENDANCE_DAYS = 60
DEMO_PASSWORD = "Passw0rd!2026"

SUBJECTS = ["CS", "MATH", "PHYS", "ENG", "BIO", "CHEM", "ECON", "HIST", "ART", "PSY", "STAT", "PHIL"]
SESSION_TYPES = ["lecture", "section", "lab", "tutorial"]
CLASS_HOURS = [9, 10, 11, 12, 13, 14, 15, 16]


# ── Step 1: Organizations ───────────────────────────────────────────────────
def seed_organizations(db: Session) -> list[Organization]:
    """Create 4 organizations (faculties/departments)."""
    names = ["Faculty of Engineering", "Faculty of Science", "Faculty of Business", "Faculty of Arts"]
    orgs = [Organization(name=n, description=fake.catch_phrase()) for n in names]
    db.add_all(orgs)
    db.commit()
    for o in orgs:
        db.refresh(o)
    return orgs


# ── Step 2: Admins ───────────────────────────────────────────────────────────
def seed_admins(db: Session, orgs: list[Organization]) -> None:
    """Create 2-3 org-scoped admin Users per organization (role='admin', matches RBAC User model, not legacy Admin table)."""
    for org in orgs:
        for _ in range(random.randint(2, 3)):
            admin = User(
                email=fake.unique.company_email(),
                hashed_password=hash_password(DEMO_PASSWORD),
                full_name=arabic_name_male() if random.random() < 0.5 else arabic_name_female(),
                role="admin",
                organization_id=org.id,
                is_active=True,
            )
            db.add(admin)
    db.commit()


# ── Step 3: Courses + Sessions ──────────────────────────────────────────────
def seed_courses(db: Session, orgs: list[Organization]) -> list[Course]:
    """Create 12 courses spread across the 4 orgs, each with 2-3 CourseSession slots on different weekdays/times."""
    courses = []
    for i in range(12):
        org = orgs[i % len(orgs)]
        subject = random.choice(SUBJECTS)
        course = Course(
            organization_id=org.id,
            name=f"{fake.catch_phrase()} {subject}",
            code=f"{subject}{random.randint(100, 499)}",
            description=fake.sentence(),
            is_active=True,
        )
        db.add(course)
        courses.append(course)
    db.commit()
    for c in courses:
        db.refresh(c)

    for course in courses:
        used_days = random.sample(range(0, 5), k=random.randint(2, 3))  # Mon-Fri, no repeats per course
        for day in used_days:
            start_hour = random.choice(CLASS_HOURS)
            session = CourseSession(
                course_id=course.id,
                session_type=random.choice(SESSION_TYPES),
                day_of_week=day,
                start_time=time(hour=start_hour, minute=0),
                end_time=time(hour=start_hour + 1, minute=0),
                late_after_minutes=15,
                is_active=True,
            )
            db.add(session)
    db.commit()
    return courses


# ── Step 4: Students (face enrollment via RecognitionPipeline + FAISS) ─────
def seed_students(db: Session, orgs: list[Organization], pipeline: RecognitionPipeline) -> list[Student]:
    """Loop dummy_faces/1..30.jpg, gender-map names (1-20 male, 21-30 female), enroll embedding in FAISS, flush+rollback DB on enrollment failure."""
    enrolled = []
    for i in range(1, 31):
        image_path = os.path.join(DUMMY_FACES_DIR, f"{i}.jpg")
        image = cv2.imread(image_path)
        if image is None:
            print(f"SKIP {i}.jpg: could not read image")
            continue

        full_name = arabic_name_male() if i <= 20 else arabic_name_female()
        org = random.choice(orgs)

        student = Student(
            name=full_name,
            student_code=f"STU{i:04d}",
            enrollment_date=fake.date_between(start_date="-2y", end_date=f"-{ATTENDANCE_DAYS}d"),
            organization_id=org.id,
        )
        db.add(student)
        db.flush()  # assigns student.id without committing, so we can roll back cleanly

        try:
            embedding = pipeline.get_embedding_for_enrollment(image)
            pipeline.index.add(student.id, embedding)
        except (FaceNotDetectedException, MultipleFacesException, ValueError, RuntimeError) as e:
            db.rollback()
            print(f"ROLLBACK student {full_name} ({i}.jpg): {e}")
            continue

        db.commit()
        db.refresh(student)
        enrolled.append(student)
        print(f"Enrolled {student.name} -> org {org.name} (student_id={student.id})")

    return enrolled


# ── Step 5: 60 days of historical attendance ────────────────────────────────
def seed_attendance(db: Session, orgs: list[Organization], courses: list[Course], students: list[Student]) -> None:
    """One attendance record per student per calendar day (matches the dashboard's Present+Late+Absent=Total assumption)."""
    students_by_org: dict[int, list[Student]] = {}
    for s in students:
        students_by_org.setdefault(s.organization_id, []).append(s)

    courses_by_org: dict[int, list[Course]] = {}
    for c in courses:
        courses_by_org.setdefault(c.organization_id, []).append(c)

    today = date.today()
    records = []

    for org in orgs:
        org_students = students_by_org.get(org.id, [])
        if not org_students:
            continue

        sessions_by_day: dict[int, list[CourseSession]] = {}
        for course in courses_by_org.get(org.id, []):
            for session in course.sessions:
                sessions_by_day.setdefault(session.day_of_week, []).append(session)

        for offset in range(ATTENDANCE_DAYS):
            day = today - timedelta(days=offset)
            day_sessions = sessions_by_day.get(day.weekday())
            if not day_sessions:
                continue  # org has no class scheduled this weekday

            for student in org_students:
                session = random.choice(day_sessions)  # exactly one record for this student today
                roll = random.random()
                if roll < 0.10:  # absent
                    records.append(Attendance(
                        student_id=student.id, course_session_id=session.id, date=day,
                        timestamp=None, status="absent", is_late=False, confidence=None,
                    ))
                elif roll < 0.25:  # late
                    late_minutes = random.randint(session.late_after_minutes, session.late_after_minutes + 30)
                    ts = datetime.combine(day, session.start_time) + timedelta(minutes=late_minutes)
                    records.append(Attendance(
                        student_id=student.id, course_session_id=session.id, date=day,
                        timestamp=ts, status="late", is_late=True,
                        confidence=round(random.uniform(0.75, 0.98), 4),
                    ))
                else:  # present
                    ts = datetime.combine(day, session.start_time) + timedelta(minutes=random.randint(-5, 10))
                    records.append(Attendance(
                        student_id=student.id, course_session_id=session.id, date=day,
                        timestamp=ts, status="present", is_late=False,
                        confidence=round(random.uniform(0.85, 0.999), 4),
                    ))

    db.bulk_save_objects(records)
    db.commit()
    print(f"Inserted {len(records)} attendance records.")


def main():
    for path in [settings.FAISS_INDEX_PATH, settings.FAISS_ID_MAP_PATH]:
        if os.path.exists(path):
            os.remove(path)
            print(f"Wiped stale FAISS file: {path}")

    db = SessionLocal()
    print("Loading RecognitionPipeline (RetinaFace + ArcFace)...")
    pipeline = RecognitionPipeline()

    try:
        orgs = seed_organizations(db)
        seed_admins(db, orgs)
        courses = seed_courses(db, orgs)
        students = seed_students(db, orgs, pipeline)
        seed_attendance(db, orgs, courses, students)
    finally:
        db.close()

    print(f"\nDone. {len(orgs)} orgs, {len(courses)} courses, {len(students)} students enrolled.")
    print(f"Demo login password for all seeded admins: {DEMO_PASSWORD}")


if __name__ == "__main__":
    main()