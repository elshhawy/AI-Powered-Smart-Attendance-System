# src/services/course_service.py
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from src.db.repositories.course_repository import CourseRepository
from src.db.repositories.course_session_repository import CourseSessionRepository
from src.models.course import Course
from src.models.course_session import CourseSession


# ── Custom Exceptions ─────────────────────────────────────────

class CourseNotFoundException(Exception):
    pass

class CourseAlreadyExistsException(Exception):
    pass

class CourseSessionNotFoundException(Exception):
    pass

class InvalidSessionTimeException(Exception):
    pass


# ── Service ───────────────────────────────────────────────────

class CourseService:

    def __init__(self, db: Session):
        self.db = db
        self.course_repo = CourseRepository(db)
        self.session_repo = CourseSessionRepository(db)

    # ── Courses ───────────────────────────────────────────────

    def create_course(
        self,
        name: str,
        code: str,
        organization_id: int,
        description: str | None = None,
    ) -> Course:
        existing = self.course_repo.get_by_code(code, organization_id)
        if existing:
            raise CourseAlreadyExistsException(
                f"A course with code '{code}' already exists in this organization."
            )
        return self.course_repo.create({
            "name": name,
            "code": code,
            "organization_id": organization_id,
            "description": description,
            "is_active": True,
        })

    def update_course(self, course_id: int, data: dict) -> Course:
        course = self.course_repo.get_by_id(course_id)
        if not course:
            raise CourseNotFoundException(f"Course {course_id} not found.")
        # Remove None values
        updates = {k: v for k, v in data.items() if v is not None}
        return self.course_repo.update(course, updates)

    def delete_course(self, course_id: int) -> bool:
        course = self.course_repo.get_by_id(course_id)
        if not course:
            raise CourseNotFoundException(f"Course {course_id} not found.")
        return self.course_repo.delete(course_id)

    def list_courses(self, org_id: int | None = None) -> list[Course]:
        if org_id is None:
            return self.course_repo.get_all()
        return self.course_repo.get_by_organization(org_id)

    def get_course(self, course_id: int) -> Course:
        course = self.course_repo.get_by_id(course_id)
        if not course:
            raise CourseNotFoundException(f"Course {course_id} not found.")
        return course

    # ── Sessions ──────────────────────────────────────────────

    def add_session(
        self,
        course_id: int,
        session_type: str,
        day_of_week: int,
        start_time,
        end_time,
        late_after_minutes: int = 15,
    ) -> CourseSession:
        # Verify course exists
        course = self.course_repo.get_by_id(course_id)
        if not course:
            raise CourseNotFoundException(f"Course {course_id} not found.")

        # Validate time range
        if end_time <= start_time:
            raise InvalidSessionTimeException(
                "end_time must be after start_time."
            )

        return self.session_repo.create({
            "course_id": course_id,
            "session_type": session_type.lower().strip(),
            "day_of_week": day_of_week,
            "start_time": start_time,
            "end_time": end_time,
            "late_after_minutes": late_after_minutes,
            "is_active": True,
        })

    def update_session(self, session_id: int, data: dict) -> CourseSession:
        session = self.session_repo.get_by_id(session_id)
        if not session:
            raise CourseSessionNotFoundException(f"Session {session_id} not found.")

        updates = {k: v for k, v in data.items() if v is not None}

        # Validate times if both provided
        new_start = updates.get("start_time", session.start_time)
        new_end = updates.get("end_time", session.end_time)
        if new_end <= new_start:
            raise InvalidSessionTimeException("end_time must be after start_time.")

        return self.session_repo.update(session, updates)

    def delete_session(self, session_id: int) -> bool:
        session = self.session_repo.get_by_id(session_id)
        if not session:
            raise CourseSessionNotFoundException(f"Session {session_id} not found.")
        return self.session_repo.delete(session_id)

    def list_sessions(self, course_id: int) -> list[CourseSession]:
        return self.session_repo.get_by_course(course_id)

    def get_active_session_now(self, org_id: int) -> CourseSession | None:
        """
        Returns the currently active session for an org based on
        current day of week and current time.
        Used by AttendanceService to determine late threshold dynamically.
        """
        now = datetime.now(timezone.utc)
        current_day = now.weekday()  # 0=Monday
        current_time = now.time().replace(tzinfo=None)
        return self.session_repo.get_active_now(org_id, current_day, current_time)