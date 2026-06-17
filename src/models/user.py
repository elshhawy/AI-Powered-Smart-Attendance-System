# src/models/user.py
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Boolean, ForeignKey, DateTime
from datetime import datetime
from src.db.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    hashed_password: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        # nullable because Google OAuth users have no password
    )

    google_id: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        # nullable because email/password users have no google_id
    )

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="admin",
        # "super_admin" | "admin" | "student"
    )

    # Only set when role = "student"
    # Links this user account to a student record
    student_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("students.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Only set when role = "admin" (binds an admin to exactly one org).
    # Null for super_admin (sees all orgs) and student (scoped via student_id).
    organization_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationship to student record
    student: Mapped["Student | None"] = relationship(
        "Student",
        foreign_keys=[student_id],
    )

    # Relationship to organization record (admin scoping)
    organization: Mapped["Organization | None"] = relationship(
        "Organization",
        foreign_keys=[organization_id],
        back_populates="users",
    )