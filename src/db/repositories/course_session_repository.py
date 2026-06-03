# src/db/repositories/course_session_repository.py
from datetime import time, datetime
from sqlalchemy.orm import Session
from src.models.course_session import CourseSession
from src.db.repositories.base import BaseRepository


class CourseSessionRepository(BaseRepository[CourseSession]):

    def __init__(self, db: Session):
        super().__init__(db, CourseSession)

    def get_by_course(self, course_id: int) -> list[CourseSession]:
        """All sessions for a course, ordered by day then start time."""
        return (
            self.db.query(CourseSession)
            .filter(CourseSession.course_id == course_id)
            .order_by(CourseSession.day_of_week, CourseSession.start_time)
            .all()
        )

    def get_active_now(
        self,
        org_id: int,
        current_day: int,
        current_time: time,
    ) -> CourseSession | None:
        """
        Find the active session for an organization right now.

        Matches sessions where:
        - Belongs to a course in this org
        - Same day of week as today
        - current_time is between start_time and end_time
        - is_active = True
        - The parent course is also active

        Returns the most recently started session if multiple match.
        """
        from src.models.course import Course

        sessions = (
            self.db.query(CourseSession)
            .join(Course, CourseSession.course_id == Course.id)
            .filter(
                Course.organization_id == org_id,
                Course.is_active == True,
                CourseSession.is_active == True,
                CourseSession.day_of_week == current_day,
                CourseSession.start_time <= current_time,
                CourseSession.end_time >= current_time,
            )
            .order_by(CourseSession.start_time.desc())
            .all()
        )

        return sessions[0] if sessions else None

    def get_by_org(self, org_id: int) -> list[CourseSession]:
        """All sessions across all courses in an organization."""
        from src.models.course import Course

        return (
            self.db.query(CourseSession)
            .join(Course, CourseSession.course_id == Course.id)
            .filter(Course.organization_id == org_id)
            .order_by(CourseSession.day_of_week, CourseSession.start_time)
            .all()
        )