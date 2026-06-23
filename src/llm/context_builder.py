# src/llm/context_builder.py
from datetime import date, timedelta, datetime
from sqlalchemy.orm import Session

from src.db.repositories.attendance_repository import AttendanceRepository
from src.db.repositories.student_repository import StudentRepository
from src.db.repositories.course_session_repository import CourseSessionRepository


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

    DAY_NAMES = {
        0: "Monday", 1: "Tuesday", 2: "Wednesday",
        3: "Thursday", 4: "Friday", 5: "Saturday", 6: "Sunday"
    }

    def __init__(self, db: Session):
        self.attendance_repo = AttendanceRepository(db)
        self.student_repo = StudentRepository(db)
        self.course_session_repo = CourseSessionRepository(db)

    def build_today_context(self, organization_id: int | None = None) -> str:
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
        if organization_id:
            all_students = self.student_repo.get_by_organization(organization_id)
        else:
            all_students = self.student_repo.get_all()

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

    def _get_active_sessions(self, organization_id: int) -> list:
        """Shared helper — all active course sessions for an org."""
        sessions = self.course_session_repo.get_by_org(organization_id)
        return [s for s in sessions if s.is_active]

    def _build_schedule_lines(self, active_sessions: list) -> list[str]:
        """
        Build the weekly schedule section as a list of text lines,
        sorted by day of week then start time.
        """
        if not active_sessions:
            return ["No weekly schedule found for this organization."]

        sorted_sessions = sorted(active_sessions, key=lambda s: (s.day_of_week, s.start_time))

        lines = []
        for s in sorted_sessions:
            day_name = self.DAY_NAMES.get(s.day_of_week, "Unknown")
            start = str(s.start_time)[:5]
            end = str(s.end_time)[:5]
            course_name = s.course.name if s.course else "Unknown course"
            lines.append(
                f"  {day_name}: {course_name} ({s.session_type}), {start}–{end}"
            )

        return lines

    def _find_next_session(self, active_sessions: list, now: datetime) -> str:
        """
        Find the next upcoming session (today later, or in the coming days),
        skipping exam sessions (those are surfaced separately).
        Returns a human-readable description.
        """
        regular_sessions = [s for s in active_sessions if s.session_type != "exam"]
        if not regular_sessions:
            return "No upcoming classes scheduled."

        current_day = now.weekday()
        current_time = now.time()

        # 1. Look for a session later today
        today_sessions = sorted(
            [s for s in regular_sessions if s.day_of_week == current_day and s.start_time > current_time],
            key=lambda s: s.start_time,
        )
        if today_sessions:
            s = today_sessions[0]
            return (
                f"Later today: {s.course.name} ({s.session_type}) "
                f"at {str(s.start_time)[:5]}"
            )

        # 2. Look for the next session in the upcoming days (wrap around the week)
        for offset in range(1, 8):
            check_day = (current_day + offset) % 7
            day_sessions = sorted(
                [s for s in regular_sessions if s.day_of_week == check_day],
                key=lambda s: s.start_time,
            )
            if day_sessions:
                s = day_sessions[0]
                day_name = self.DAY_NAMES.get(check_day, "Unknown")
                return (
                    f"Next class: {s.course.name} ({s.session_type}) "
                    f"on {day_name} at {str(s.start_time)[:5]}"
                )

        return "No upcoming classes scheduled."

    def _build_per_course_attendance(self, records: list) -> list[str]:
        """
        Break down the student's attendance by course, including an
        at-risk flag for any individual course below 75%, even if
        their overall attendance looks fine.
        """
        course_stats: dict[str, dict] = {}
        for r in records:
            course_name = "Unassigned sessions"
            if r.course_session_id and r.course_session and r.course_session.course:
                course_name = r.course_session.course.name

            stats = course_stats.setdefault(course_name, {"present": 0, "late": 0, "absent": 0, "total": 0})
            stats["total"] += 1
            if r.status == "absent":
                stats["absent"] += 1
            elif r.is_late:
                stats["late"] += 1
            else:
                stats["present"] += 1

        if not course_stats:
            return []

        lines = ["\nAttendance by course:"]
        for course_name, stats in sorted(course_stats.items()):
            pct = round(((stats["present"] + stats["late"]) / stats["total"] * 100) if stats["total"] else 0, 1)
            risk_flag = " — AT RISK (below 75%)" if pct < 75 else ""
            lines.append(
                f"  {course_name}: {pct}% attendance "
                f"({stats['present']} present, {stats['late']} late, {stats['absent']} absent){risk_flag}"
            )

        return lines

    def _build_exam_lines(self, active_sessions: list) -> list[str]:
        """
        Surface any scheduled exam sessions, if present in the data.
        """
        exam_sessions = [s for s in active_sessions if s.session_type == "exam"]
        if not exam_sessions:
            return []

        sorted_exams = sorted(exam_sessions, key=lambda s: (s.day_of_week, s.start_time))
        lines = ["\nScheduled exams:"]
        for s in sorted_exams:
            day_name = self.DAY_NAMES.get(s.day_of_week, "Unknown")
            start = str(s.start_time)[:5]
            course_name = s.course.name if s.course else "Unknown course"
            lines.append(f"  {course_name}: {day_name} at {start}")

        return lines

    def build_student_context(self, student_id: int) -> str:
        """
        Build a text summary of a single student's own attendance data,
        their weekly class schedule, per-course attendance breakdown,
        the next upcoming class, and any scheduled exams. Used for the
        student-facing chatbot — only their own info, nothing about
        other students is ever included here.
        """
        student = self.student_repo.get_by_id(student_id)
        if not student:
            return "Student record not found."

        records = self.attendance_repo.get_by_student(student_id)

        total = len(records)
        present = sum(1 for r in records if r.status == "present" and not r.is_late)
        late = sum(1 for r in records if r.is_late)
        absent = sum(1 for r in records if r.status == "absent")
        percentage = round(((present + late) / total * 100) if total else 0, 1)

        now = datetime.now()

        lines = [
            f"Today is: {self.DAY_NAMES.get(now.weekday(), 'Unknown')}, {now.strftime('%H:%M')}",
            f"Student name: {student.name}",
            f"Student code: {student.student_code}",
            f"Total attendance records: {total}",
            f"Present on time: {present}",
            f"Late: {late}",
            f"Absent: {absent}",
            f"Overall attendance rate: {percentage}%",
            "",
        ]

        if percentage < 75:
            lines.append("Note: This student's overall attendance is below the required 75% threshold.")

        # Recent records (last 10), most recent first
        recent = sorted(records, key=lambda r: r.date, reverse=True)[:10]
        if recent:
            lines.append("\nRecent attendance history:")
            for r in recent:
                status_label = "Late" if r.is_late else ("Absent" if r.status == "absent" else "Present")
                course_name = ""
                if r.course_session_id and r.course_session and r.course_session.course:
                    course_name = f" — {r.course_session.course.name}"
                lines.append(f"  {r.date.strftime('%Y-%m-%d')}: {status_label}{course_name}")

        # Per-course attendance breakdown (point 2 & 3)
        lines.extend(self._build_per_course_attendance(records))

        # Schedule data, shared across the next few sections
        active_sessions = self._get_active_sessions(student.organization_id)

        # Next upcoming class (point 1)
        lines.append(f"\n{self._find_next_session(active_sessions, now)}")

        # Full weekly schedule
        lines.append("\nWeekly class schedule:")
        lines.extend(self._build_schedule_lines(active_sessions))

        # Scheduled exams, if any (point 4)
        lines.extend(self._build_exam_lines(active_sessions))

        return "\n".join(lines)