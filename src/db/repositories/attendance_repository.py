# src/db/repositories/attendance_repository.py
from datetime import date
from sqlalchemy.orm import Session
from src.models.attendance import Attendance
from src.db.repositories.base import BaseRepository


class AttendanceRepository(BaseRepository[Attendance]):

    def __init__(self, db: Session):
        super().__init__(db, Attendance)

    def check_duplicate(
        self,
        student_id: int,
        check_date: date,
        course_session_id: int | None = None,
    ) -> bool:
        """
        Check if attendance already recorded for today.

        If course_session_id is provided: check per-session duplicate
        (student can attend lecture AND section on the same day).

        If no course_session_id: check if ANY record exists today
        (backward compatible with old records).
        """
        query = self.db.query(Attendance).filter(
            Attendance.student_id == student_id,
            Attendance.date == check_date,
        )

        if course_session_id is not None:
            query = query.filter(Attendance.course_session_id == course_session_id)

        return query.first() is not None

    def get_by_student(self, student_id: int) -> list[Attendance]:
        return (
            self.db.query(Attendance)
            .filter(Attendance.student_id == student_id)
            .order_by(Attendance.date.desc())
            .all()
        )

    def get_by_date_range(
        self,
        date_from: date,
        date_to: date,
        org_id: int | None = None,
        course_session_id: int | None = None,
    ) -> list[Attendance]:
        """
        All records between two dates.
        Optionally filtered by org_id and/or course_session_id.
        """
        from src.models.student import Student

        query = self.db.query(Attendance).filter(
            Attendance.date >= date_from,
            Attendance.date <= date_to,
        )

        if org_id is not None:
            query = query.join(Student).filter(Student.organization_id == org_id)

        if course_session_id is not None:
            query = query.filter(Attendance.course_session_id == course_session_id)

        return query.order_by(Attendance.date.desc()).all()

    def get_absences_today(self) -> list[Attendance]:
        return (
            self.db.query(Attendance)
            .filter(Attendance.date == date.today(), Attendance.status == "absent")
            .all()
        )

    def get_late_today(self) -> list[Attendance]:
        return (
            self.db.query(Attendance)
            .filter(Attendance.date == date.today(), Attendance.is_late == True)
            .all()
        )

    def get_attendance_percentage(self, student_id: int) -> float:
        total = (
            self.db.query(Attendance)
            .filter(Attendance.student_id == student_id)
            .count()
        )
        if total == 0:
            return 0.0
        present = (
            self.db.query(Attendance)
            .filter(
                Attendance.student_id == student_id,
                Attendance.status.in_(["present", "late"]),
            )
            .count()
        )
        return (present / total) * 100.0

    def mark_absent(self, student_id: int, mark_date: date) -> Attendance:
        return self.create({
            "student_id": student_id,
            "course_session_id": None,
            "date": mark_date,
            "status": "absent",
            "is_late": False,
            "confidence": None,
            "timestamp": None,
        })