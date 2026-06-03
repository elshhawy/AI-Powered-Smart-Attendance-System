# src/models/attendance.py
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey, DateTime, String, Float, Date, Boolean
from datetime import datetime, date
from src.db.database import Base


class Attendance(Base):
    __tablename__ = "attendance"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # NEW: Link attendance to a specific course session
    # nullable=True for backward compatibility — old records have no session
    course_session_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("course_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    timestamp: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # NULL for absent records (student never arrived)

    status: Mapped[str] = mapped_column(String(20), nullable=False)
    # "present" | "late" | "absent"

    is_late: Mapped[bool] = mapped_column(Boolean, default=False)

    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    # NULL for manually-entered absent records

    # Relationships
    student: Mapped["Student"] = relationship(
        "Student",
        back_populates="attendance_records",
        passive_deletes=True,
    )

    course_session: Mapped["CourseSession | None"] = relationship(
        "CourseSession",
        back_populates="attendance_records",
    )