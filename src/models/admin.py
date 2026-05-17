# src/models/admin.py
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean, DateTime
from datetime import datetime
from src.db.database import Base


class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,   # Unique identifier. PostgreSQL auto-increments this.
        index=True          # Creates an index so lookups by id are fast.
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,        # No two admins can have the same email.
        nullable=False,     # Every admin must have an email.
        index=True          # Indexed because login looks up admin by email.
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False      # bcrypt hash, never the plain password.
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True        # New admins are active by default.
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow  # Set automatically when the row is created.
    )

    # NOTICE: No role_id. No student_id. No foreign keys to anything.
    # An admin is a standalone account. They manage the system.
    # They are not a student. They have no "profile" beyond this row.