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
        ForeignKey("students.id"),  # Links to the students table.
        nullable=False,
        index=True   # Indexed because the most common query is:
                     # "give me all attendance records for student X"
                     # Without this index, PostgreSQL scans the whole table.
    )

    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True   # Also indexed because we query by date a lot:
                     # "give me all records for today"
    )

    timestamp: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
        # WHY nullable? Because there are two kinds of attendance records:
        #   1. Camera-detected: timestamp = when they walked past the camera
        #   2. Manually entered (absent): timestamp = NULL because they never arrived
        # Both kinds share this same table. date is always set, timestamp is sometimes NULL.
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False
        # Only three possible values: "present", "late", "absent"
        # "present" = arrived before the late threshold
        # "late"    = arrived after the late threshold
        # "absent"  = never arrived (manually entered or via daily job)
    )

    is_late: Mapped[bool] = mapped_column(Boolean, default=False)
    # True when status is "late". Stored separately so you can query
    # "count of late arrivals" without string matching on status.

    confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
        # The confidence score from FAISS (0.0 to 1.0).
        # NULL for manually-entered absent records — no AI was involved.
        # Example value: 0.94 means "94% certain this is the right person"
    )

    # Relationship:
    student: Mapped["Student"] = relationship(
        "Student",
        back_populates="attendance_records"
        # Lets you write: record.student → gives you the Student object
    )