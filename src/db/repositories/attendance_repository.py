# src/db/repositories/attendance_repository.py
from datetime import date
from sqlalchemy.orm import Session
from src.models.attendance import Attendance
from src.db.repositories.base import BaseRepository


class AttendanceRepository(BaseRepository[Attendance]):

    def __init__(self, db: Session):
        super().__init__(db, Attendance)

    def check_duplicate(self, student_id: int, check_date: date) -> bool:
        """
        Returns True if an attendance record already exists for this student today.

        This is called BEFORE creating any new record.
        If a student walks past the camera twice, we only record it once.
        The second pass returns "already_marked" without creating a duplicate.
        """
        existing = (
            self.db.query(Attendance)
            .filter(
                Attendance.student_id == student_id,
                Attendance.date == check_date
            )
            .first()
        )
        return existing is not None

    def get_by_student(self, student_id: int) -> list[Attendance]:
        """All attendance records for one student, newest first."""
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
        org_id: int | None = None
    ) -> list[Attendance]:
        """
        All records between two dates, optionally filtered by organization.
        Used by the reports page and the chatbot context builder.

        The join with Student is only added when org_id is provided,
        because joining adds overhead even when you don't filter on it.
        """
        from src.models.student import Student

        query = self.db.query(Attendance).filter(
            Attendance.date >= date_from,
            Attendance.date <= date_to
        )

        if org_id is not None:
            query = query.join(Student).filter(
                Student.organization_id == org_id
            )

        return query.order_by(Attendance.date.desc()).all()

    def get_absences_today(self) -> list[Attendance]:
        """All absent records for today. Used by the chatbot."""
        return (
            self.db.query(Attendance)
            .filter(
                Attendance.date == date.today(),
                Attendance.status == "absent"
            )
            .all()
        )

    def get_late_today(self) -> list[Attendance]:
        """All late arrivals for today. Used by the chatbot."""
        return (
            self.db.query(Attendance)
            .filter(
                Attendance.date == date.today(),
                Attendance.is_late == True
            )
            .all()
        )

    def get_attendance_percentage(self, student_id: int) -> float:
        """
        Returns the attendance percentage for one student across all time.
        Used to find at-risk students (below 75%).

        Formula: (present + late) / total × 100
        We count "late" as present because the student did show up.
        """
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
                Attendance.status.in_(["present", "late"])
            )
            .count()
        )

        return (present / total) * 100.0

    def mark_absent(self, student_id: int, mark_date: date) -> Attendance:
        """
        Manually create an absence record.
        Used by a daily job that runs at end-of-day and marks anyone
        who never appeared on camera as absent.

        Note the None values: no timestamp (never arrived), no confidence (no AI).
        """
        return self.create({
            "student_id": student_id,
            "date":       mark_date,
            "status":     "absent",
            "is_late":    False,
            "confidence": None,
            "timestamp":  None,
        })