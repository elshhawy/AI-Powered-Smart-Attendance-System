# scripts/test_data_layer.py
# Run this from the project root: python scripts/test_data_layer.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date
from src.db.database import SessionLocal
from src.db.repositories.admin_repository import AdminRepository
from src.db.repositories.student_repository import StudentRepository
from src.db.repositories.attendance_repository import AttendanceRepository

# We need bcrypt for hashing — just for this test
# If you haven't installed it yet: pip install passlib[bcrypt]
try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    def hash_password(p): return pwd_context.hash(p)
except ImportError:
    def hash_password(p): return "hashed_" + p  # Placeholder for testing

def run():
    print("=" * 50)
    print("Phase 1 Data Layer Test")
    print("=" * 50)

    db = SessionLocal()
    admin_r  = AdminRepository(db)
    student_r = StudentRepository(db)
    attend_r  = AttendanceRepository(db)

    # ── Test 1: Create an organization ───────────────────────────────────
    print("\n[1] Creating test organization...")
    from src.models.organization import Organization
    org = db.query(Organization).filter(
        Organization.name == "Test Faculty"
    ).first()
    if not org:
        org = Organization(name="Test Faculty", description="For testing")
        db.add(org)
        db.commit()
        db.refresh(org)
    print(f"    ✓ Organization: '{org.name}' (id={org.id})")

    # ── Test 2: Create an admin ───────────────────────────────────────────
    print("\n[2] Creating test admin...")
    admin = admin_r.get_by_email("test_admin@uni.edu")
    if not admin:
        admin = admin_r.create({
            "email":           "test_admin@uni.edu",
            "hashed_password": hash_password("testpassword"),
            "full_name":       "Test Admin",
        })
    print(f"    ✓ Admin: '{admin.full_name}' (id={admin.id})")

    # ── Test 3: Lookup admin by email ─────────────────────────────────────
    print("\n[3] Looking up admin by email...")
    found = admin_r.get_by_email("test_admin@uni.edu")
    assert found is not None, "Admin not found by email!"
    assert found.id == admin.id
    print(f"    ✓ Found by email: '{found.email}'")

    # ── Test 4: Create a student (no user_id!) ────────────────────────────
    print("\n[4] Creating test student (no user_id, no password)...")
    student = student_r.get_by_code("TEST001")
    if not student:
        student = student_r.create({
            "name":            "Ahmed Khaled",
            "student_code":    "TEST001",
            "enrollment_date": date.today(),
            "organization_id": org.id,
        })
    print(f"    ✓ Student: '{student.name}' (id={student.id})")

    # Verify no user_id column exists
    assert not hasattr(student, 'user_id'), \
        "FAIL: Student has user_id — should not exist in this design!"
    print("    ✓ Confirmed: student has no user_id column")

    # ── Test 5: Search student by name ────────────────────────────────────
    print("\n[5] Searching student by partial name...")
    results = student_r.search_by_name("ahmed")
    assert len(results) >= 1
    print(f"    ✓ Found {len(results)} student(s) matching 'ahmed'")

    # ── Test 6: Mark attendance ───────────────────────────────────────────
    print("\n[6] Marking attendance...")
    # First check — should be no record yet
    today_has_record = attend_r.check_duplicate(student.id, date.today())

    if not today_has_record:
        record = attend_r.create({
            "student_id": student.id,
            "date":       date.today(),
            "timestamp":  None,      # Would be datetime.utcnow() from camera
            "status":     "present",
            "is_late":    False,
            "confidence": 0.94,
        })
        print(f"    ✓ Attendance record created (id={record.id})")
    else:
        print("    ✓ Record already exists from a previous run")

    # ── Test 7: Duplicate check ───────────────────────────────────────────
    print("\n[7] Checking duplicate prevention...")
    is_duplicate = attend_r.check_duplicate(student.id, date.today())
    assert is_duplicate == True, "Duplicate check failed!"
    print("    ✓ Duplicate correctly detected — second mark would be blocked")

    # ── Test 8: Attendance percentage ─────────────────────────────────────
    print("\n[8] Calculating attendance percentage...")
    pct = attend_r.get_attendance_percentage(student.id)
    assert pct == 100.0, f"Expected 100.0, got {pct}"
    print(f"    ✓ Attendance: {pct:.1f}%")

    # ── Test 9: Get all students in organization ───────────────────────────
    print("\n[9] Getting all students in organization...")
    org_students = student_r.get_by_organization(org.id)
    assert len(org_students) >= 1
    print(f"    ✓ Found {len(org_students)} student(s) in '{org.name}'")

    # ── Cleanup ───────────────────────────────────────────────────────────
    print("\n[Cleanup] Removing test data...")
    records = attend_r.get_by_student(student.id)
    for r in records:
        attend_r.delete(r.id)
    student_r.delete(student.id)
    admin_r.delete(admin.id)
    db.delete(org)
    db.commit()
    db.close()

    print("\n" + "=" * 50)
    print("✅ ALL TESTS PASSED — Phase 1 is working correctly!")
    print("=" * 50)

if __name__ == "__main__":
    run()