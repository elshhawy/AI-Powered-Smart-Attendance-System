# src/models/course_session.py
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Boolean, ForeignKey, Time
from datetime import time
from src.db.database import Base


# Valid session types — open-ended so admin can add custom ones
DEFAULT_SESSION_TYPES = ["lecture", "section", "lab", "tutorial", "exam"]

DAY_NAMES = {
    0: "Monday",
    1: "Tuesday",
    2: "Wednesday",
    3: "Thursday",
    4: "Friday",
    5: "Saturday",
    6: "Sunday",
}


class CourseSession(Base):
    __tablename__ = "course_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    course_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    session_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        # "lecture" | "section" | "lab" | "tutorial" | "exam" | custom
    )

    day_of_week: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        # 0=Monday, 1=Tuesday, ..., 6=Sunday
    )

    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    # e.g. 10:00

    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    # e.g. 11:00

    late_after_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=15,
        # How many minutes after start_time = late
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    course: Mapped["Course"] = relationship("Course", back_populates="sessions")

    attendance_records: Mapped[list["Attendance"]] = relationship(
        "Attendance",
        back_populates="course_session",
        passive_deletes=True,
    )