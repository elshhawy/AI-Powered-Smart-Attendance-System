# src/services/attendance_service.py
from datetime import date, datetime, time, timezone
import numpy as np
from sqlalchemy.orm import Session

from src.ai.recognition_pipeline import RecognitionPipeline, RecognitionResult, RecognitionFailure
from src.db.repositories.attendance_repository import AttendanceRepository
from src.db.repositories.student_repository import StudentRepository
from src.db.repositories.course_session_repository import CourseSessionRepository
from src.core.config import settings
from src.models.attendance import Attendance
from src.models.course_session import CourseSession
from fastapi import HTTPException

# ── Custom Exceptions ─────────────────────────────────────────

class UnknownFaceException(Exception):
    pass

class SpoofDetectedException(Exception):
    pass


# ── Attendance Result ─────────────────────────────────────────

class AttendanceRecord:
    def __init__(
        self,
        student_id: int,
        student_name: str,
        is_late: bool,
        confidence: float,
        already_marked: bool = False,
        course_name: str | None = None,
        session_type: str | None = None,
    ):
        self.student_id = student_id
        self.student_name = student_name
        self.is_late = is_late
        self.confidence = confidence
        self.already_marked = already_marked
        self.course_name = course_name
        self.session_type = session_type


# ── Service ───────────────────────────────────────────────────

class AttendanceService:

    def __init__(self, db: Session, pipeline: RecognitionPipeline):
        self.db = db
        self.pipeline = pipeline
        self.attendance_repo = AttendanceRepository(db)
        self.student_repo = StudentRepository(db)
        self.session_repo = CourseSessionRepository(db)

    # ── Core: process camera frame ────────────────────────────

    def process_frame(self, frame: np.ndarray, org_id: int | None = None) -> AttendanceRecord:
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
# --- NEW SECURITY CHECK ---
        if org_id is not None and student.organization_id != org_id:
            # The AI found a face, but it belongs to a different school/org!
            raise HTTPException(
                status_code=403, 
                detail="Face matched a student in a different organization. Access denied."
            )
        # --------------------------
        today = date.today()
        now = datetime.now(timezone.utc)

        # Step 4 — Detect active course session (NEW)
        active_session: CourseSession | None = None
        if org_id:
            current_day = now.weekday()
            current_time = now.time().replace(tzinfo=None)
            active_session = self.session_repo.get_active_now(
                org_id=org_id,
                current_day=current_day,
                current_time=current_time,
            )

        # Step 5 — Check for duplicate attendance today
        # If active session: check duplicate per session (student can attend multiple sessions same day)
        already_marked = self.attendance_repo.check_duplicate(
            student_id=student.id,
            check_date=today,
            course_session_id=active_session.id if active_session else None,
        )

        if already_marked:
            return AttendanceRecord(
                student_id=student.id,
                student_name=student.name,
                is_late=False,
                confidence=result.confidence,
                already_marked=True,
                course_name=active_session.course.name if active_session else None,
                session_type=active_session.session_type if active_session else None,
            )

        # Step 6 — Determine if late (dynamic or fallback to .env)
        is_late = self._is_late(now, active_session)

        # Step 7 — Save attendance record
        self.attendance_repo.create({
            "student_id": student.id,
            "course_session_id": active_session.id if active_session else None,
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
            course_name=active_session.course.name if active_session else None,
            session_type=active_session.session_type if active_session else None,
        )

    # ── Queries ───────────────────────────────────────────────

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
        students = self.student_repo.get_by_organization(organization_id)
        today = date.today()
        count = 0
        for student in students:
            already_recorded = self.attendance_repo.check_duplicate(
                student_id=student.id,
                check_date=today,
            )
            if not already_recorded:
                self.attendance_repo.mark_absent(student_id=student.id, mark_date=today)
                count += 1
        return count

    def get_student_statistics(self, student_id: int, start_date: date, end_date: date) -> dict:
        all_records = self.attendance_repo.get_by_date_range(
            date_from=start_date,
            date_to=end_date,
        )
        records = [r for r in all_records if r.student_id == student_id]
        total = len(records)
        present_days = sum(1 for r in records if r.status == "present")
        late_days = sum(1 for r in records if r.is_late)
        percentage = (present_days / total * 100) if total > 0 else 0.0
        return {
            "attendance_percentage": round(percentage, 2),
            "total_days": total,
            "present_days": present_days,
            "late_days": late_days,
        }

    # ── Private helpers ───────────────────────────────────────

    def _is_late(self, now: datetime, active_session: CourseSession | None) -> bool:
        """
        Determine if the student is late.

        Priority:
        1. If there's an active course session → use its start_time + late_after_minutes
        2. Otherwise → fallback to .env settings (backward compatible)
        """
        if active_session:
            # Dynamic: use session's own late threshold
            from datetime import timedelta
            session_start = datetime.combine(date.today(), active_session.start_time)
            late_cutoff = session_start + timedelta(minutes=active_session.late_after_minutes)
            now_naive = now.replace(tzinfo=None)
            return now_naive > late_cutoff

        # Fallback: use .env values
        late_minute = settings.SESSION_START_MINUTE + settings.LATE_THRESHOLD_MINUTES
        late_hour = settings.SESSION_START_HOUR + (late_minute // 60)
        late_minute = late_minute % 60
        late_time = time(hour=late_hour, minute=late_minute)
        return now.time().replace(tzinfo=None) > late_time