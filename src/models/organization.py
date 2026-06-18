# src/models/organization.py
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Text
from src.db.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
        # Examples: "Faculty of Engineering", "Year 2 CS", "Class B Morning"
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True       # Optional. The | None means it can be None in Python.
    )

    # Relationship: one organization → many students.
    # This is NOT a column in the database. SQLAlchemy uses it to let you write:
    #   org.students   → gives you a list of Student objects in this org
    # back_populates="organization" means the Student model has a matching
    # relationship pointing back here.
    students: Mapped[list["Student"]] = relationship(
        "Student",
        back_populates="organization"
    )

    # One organization → many admin users scoped to it.
    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="organization"
    )