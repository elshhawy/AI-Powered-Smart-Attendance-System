# src/models/student.py
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, ForeignKey, Date
from datetime import date
from src.db.database import Base


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    student_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False
    )

    enrollment_date: Mapped[date] = mapped_column(Date, nullable=False)

    organization_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=False
    )

    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="students"
    )

    attendance_records: Mapped[list["Attendance"]] = relationship(
        "Attendance",
        back_populates="student",
        cascade="all, delete-orphan",  
        passive_deletes=True,
    )