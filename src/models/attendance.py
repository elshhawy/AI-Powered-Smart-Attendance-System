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
        index=True
    )

    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    timestamp: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    status: Mapped[str] = mapped_column(String(20), nullable=False)

    is_late: Mapped[bool] = mapped_column(Boolean, default=False)

    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    student: Mapped["Student"] = relationship(
        "Student",
        back_populates="attendance_records",
        passive_deletes=True,  
    )