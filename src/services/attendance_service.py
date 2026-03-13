# src/services/attendance_service.py
from datetime import date, datetime, time
import numpy as np
from sqlalchemy.orm import Session

from src.ai.recognition_pipeline import RecognitionPipeline, RecognitionResult, RecognitionFailure
from src.db.repositories.attendance_repository import AttendanceRepository
from src.db.repositories.student_repository import StudentRepository
from src.core.config import settings
from src.models.attendance import Attendance


# ── Custom Exceptions ─────────────────────────────────────────────────────────

class UnknownFaceException(Exception):
    """Raised when the face is not recognised in the FAISS index."""
    pass


class SpoofDetectedException(Exception):
    """Raised when anti-spoofing detects a fake face."""
    pass


# ── Attendance Result ─────────────────────────────────────────────────────────

class AttendanceRecord:
    def __init__(
        self,
        student_id: int,
        student_name: str,
        is_late: bool,
        confidence: float,
        already_marked: bool = False,
    ):
        self.student_id = student_id
        self.student_name = student_name
        self.is_late = is_late
        self.confidence = confidence
        self.already_marked = already_marked


# ── Service ───────────────────────────────────────────────────────────────────

class AttendanceService:

    def __init__(self, db: Session):
        self.db = db
        self.attendance_repo = AttendanceRepository(db)
        self.student_repo = StudentRepository(db)
        self.pipeline = RecognitionPipeline()

    def process_frame(self, frame: np.ndarray) -> AttendanceRecord:
        # Step 1 — Run AI pipeline
        result = self.pipeline.recognize(frame)

        # Step 2 — Handle AI failure
        if isinstance(result, RecognitionFailure):
            if "spoof" in result.reason.lower():
                raise SpoofDetectedException(result.reason)
            raise UnknownFaceException(result.reason)

        # Step 3 — Get student from PostgreSQL
        student = self.student_repo.get_by_id(result.student_id)
        if not student:
            raise UnknownFaceException(
                f"Student id {result.student_id} found in FAISS but not in database."
            )

        today = date.today()
        now = datetime.now()

        # Step 4 — Check for duplicate attendance
        already_marked = self.attendance_repo.check_duplicate(
            student_id=student.id,
            check_date=today,
        )

        if already_marked:
            return AttendanceRecord(
                student_id=student.id,
                student_name=student.name,
                is_late=False,
                confidence=result.confidence,
                already_marked=True,
            )

        # Step 5 — Determine if late
        is_late = self._is_late(now)

        # Step 6 — Save attendance to PostgreSQL
        self.attendance_repo.create({
            "student_id": student.id,
            "date": today,
            "timestamp": now,
            "status": "present",
            "is_late": is_late,
            "confidence": result.confidence,
        })

        return AttendanceRecord(
            student_id=student.id,
            student_name=student.name,
            is_late=is_late,
            confidence=result.confidence,
            already_marked=False,
        )

    def get_today_attendance(self, organization_id: int) -> list[Attendance]:
        today = date.today()
        return self.attendance_repo.get_by_date_range(
            date_from=today,
            date_to=today,
            org_id=organization_id,
        )

    def get_attendance_range(
        self,
        organization_id: int,
        start_date: date,
        end_date: date,
    ) -> list[Attendance]:
        return self.attendance_repo.get_by_date_range(
            date_from=start_date,
            date_to=end_date,
            org_id=organization_id,
        )

    def mark_absents(self, organization_id: int) -> int:
        # Get all students in organization
        students = self.student_repo.get_by_organization(organization_id)
        today = date.today()
        count = 0

        for student in students:
            # Only mark absent if no record exists for today
            already_recorded = self.attendance_repo.check_duplicate(
                student_id=student.id,
                check_date=today,
            )
            if not already_recorded:
                self.attendance_repo.mark_absent(
                    student_id=student.id,
                    mark_date=today,
                )
                count += 1

        return count

    def get_student_statistics(self, student_id: int, start_date: date, end_date: date) -> dict:
        records = self.attendance_repo.get_by_date_range(
            date_from=start_date,
            date_to=end_date,
        )
        # Filter for this student only
        student_records = [r for r in records if r.student_id == student_id]

        total = len(student_records)
        present_days = sum(1 for r in student_records if r.status == "present")
        late_days = sum(1 for r in student_records if r.is_late)
        percentage = (present_days / total * 100) if total > 0 else 0.0

        return {
            "attendance_percentage": round(percentage, 2),
            "total_days": total,
            "present_days": present_days,
            "late_days": late_days,
        }

    def _is_late(self, now: datetime) -> bool:
        late_minute = settings.SESSION_START_MINUTE + settings.LATE_THRESHOLD_MINUTES
        late_hour = settings.SESSION_START_HOUR + (late_minute // 60)
        late_minute = late_minute % 60

        late_time = time(hour=late_hour, minute=late_minute)
        return now.time() > late_time