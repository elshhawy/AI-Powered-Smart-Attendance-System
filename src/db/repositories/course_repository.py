# src/db/repositories/course_repository.py
from sqlalchemy.orm import Session
from src.models.course import Course
from src.db.repositories.base import BaseRepository


class CourseRepository(BaseRepository[Course]):

    def __init__(self, db: Session):
        super().__init__(db, Course)

    def get_by_organization(self, org_id: int) -> list[Course]:
        """All courses for an organization, ordered by name."""
        return (
            self.db.query(Course)
            .filter(Course.organization_id == org_id)
            .order_by(Course.name)
            .all()
        )

    def get_active_by_organization(self, org_id: int) -> list[Course]:
        """Only active courses for an organization."""
        return (
            self.db.query(Course)
            .filter(
                Course.organization_id == org_id,
                Course.is_active == True,
            )
            .order_by(Course.name)
            .all()
        )

    def get_by_code(self, code: str, org_id: int) -> Course | None:
        """Find course by code within an organization."""
        return (
            self.db.query(Course)
            .filter(
                Course.code == code,
                Course.organization_id == org_id,
            )
            .first()
        )