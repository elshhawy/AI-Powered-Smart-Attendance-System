# src/llm/context_builder.py
from datetime import date, timedelta
from sqlalchemy.orm import Session

from src.db.repositories.attendance_repository import AttendanceRepository
from src.db.repositories.student_repository import StudentRepository


class ContextBuilder:
    """
    Builds a text summary of today's attendance data.
    This summary is passed to the LLM as context (RAG).

    Why RAG?
        The LLM doesn't have access to our database.
        We pull the relevant data, format it as text,
        and inject it into the prompt — so the LLM can
        answer questions about OUR students.
    """

    def __init__(self, db: Session):
        self.attendance_repo = AttendanceRepository(db)
        self.student_repo = StudentRepository(db)

    def build_today_context(self, organization_id: int) -> str:
        """
        Build a text summary of today's attendance for the LLM.
        """
        today = date.today()

        # Get today's attendance records
        records = self.attendance_repo.get_by_date_range(
            date_from=today,
            date_to=today,
            org_id=organization_id,
        )

        # Get all students in the org
        all_students = self.student_repo.get_by_organization(organization_id)

        if not all_students:
            return "No students found in this organization."

        # Separate present, late, absent
        present_ids = {r.student_id for r in records if r.status == "present" and not r.is_late}
        late_ids = {r.student_id for r in records if r.is_late}
        absent_ids = {s.id for s in all_students} - present_ids - late_ids

        # Build student name maps
        student_map = {s.id: s.name for s in all_students}

        present_names = [student_map[i] for i in present_ids if i in student_map]
        late_names = [student_map[i] for i in late_ids if i in student_map]
        absent_names = [student_map[i] for i in absent_ids if i in student_map]

        # Build context string
        lines = [
            f"Date: {today.strftime('%A, %B %d, %Y')}",
            f"Total students: {len(all_students)}",
            f"Present on time: {len(present_names)}",
            f"Late: {len(late_names)}",
            f"Absent: {len(absent_names)}",
            f"Attendance rate: {round((len(present_names) + len(late_names)) / len(all_students) * 100, 1)}%",
            "",
        ]

        if present_names:
            lines.append(f"Present students: {', '.join(sorted(present_names))}")
        if late_names:
            lines.append(f"Late students: {', '.join(sorted(late_names))}")
        if absent_names:
            lines.append(f"Absent students: {', '.join(sorted(absent_names))}")

        return "\n".join(lines)

    def build_week_context(self, organization_id: int) -> str:
        """
        Build a summary of this week's attendance.
        """
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

        records = self.attendance_repo.get_by_date_range(
            date_from=week_start,
            date_to=today,
            org_id=organization_id,
        )

        all_students = self.student_repo.get_by_organization(organization_id)
        if not all_students:
            return "No students found in this organization."

        student_map = {s.id: s.name for s in all_students}

        # Count attendance per student this week
        student_counts: dict[int, int] = {}
        for r in records:
            if r.status in ("present",):
                student_counts[r.student_id] = student_counts.get(r.student_id, 0) + 1

        # Find at-risk students (attended less than 60% of days this week)
        days_so_far = (today - week_start).days + 1
        threshold = days_so_far * 0.6
        at_risk = [
            student_map[sid]
            for sid in [s.id for s in all_students]
            if student_counts.get(sid, 0) < threshold
        ]

        lines = [
            f"Week: {week_start.strftime('%B %d')} → {today.strftime('%B %d, %Y')}",
            f"Days tracked: {days_so_far}",
            f"Total students: {len(all_students)}",
            f"Total attendance records: {len(records)}",
            "",
        ]

        if at_risk:
            lines.append(f"At-risk students (low attendance this week): {', '.join(sorted(at_risk))}")
        else:
            lines.append("No at-risk students this week.")

        return "\n".join(lines)