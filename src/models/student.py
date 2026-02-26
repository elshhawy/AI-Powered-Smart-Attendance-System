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
        unique=True,    # No two students can have the same code.
        nullable=False
    )

    enrollment_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Foreign key: links this student to one organization.
    # "organizations.id" means: look at the organizations table, column id.
    organization_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=False
    )

    # Relationships (not database columns):
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="students"
        # Lets you write: student.organization → gives you the Organization object
    )
    attendance_records: Mapped[list["Attendance"]] = relationship(
        "Attendance",
        back_populates="student"
        # Lets you write: student.attendance_records → list of all their records
    )

    # ════════════════════════════════════════════════════════════════════
    # THE MOST IMPORTANT THING ABOUT THIS FILE:
    #
    # There is no user_id column.
    # There is no email column.
    # There is no hashed_password column.
    # There is no is_active column.
    #
    # A Student is not a user. They cannot log in. They are identified
    # at attendance time by their face embedding stored in FAISS,
    # which points back to this student's id.
    # ════════════════════════════════════════════════════════════════════