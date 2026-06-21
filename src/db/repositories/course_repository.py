# src/db/repositories/course_repository.py
from sqlalchemy.orm import Session
from src.models.course import Course
from src.db.repositories.base import BaseRepository


class CourseRepository(BaseRepository[Course]):

    def __init__(self, db: Session):
        super().__init__(db, Course)

    def get_all_scoped(
        self,
        organization_id: int | None = None,
        skip: int = 0,
        limit: int = 200,
    ) -> list[Course]:
        """Return courses filtered by org for regular admins; all for super_admin."""
        q = self.db.query(Course)
        if organization_id is not None:
            q = q.filter(Course.organization_id == organization_id)
        return q.order_by(Course.name).offset(skip).limit(limit).all()

    def get_by_id_scoped(
        self,
        course_id: int,
        organization_id: int | None = None,
    ) -> Course | None:
        """Fetch one course, enforcing org scope for regular admins."""
        q = self.db.query(Course).filter(Course.id == course_id)
        if organization_id is not None:
            q = q.filter(Course.organization_id == organization_id)
        return q.first()

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