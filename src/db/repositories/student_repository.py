# src/db/repositories/student_repository.py
from sqlalchemy.orm import Session
from src.models.student import Student
from src.db.repositories.base import BaseRepository


class StudentRepository(BaseRepository[Student]):

    def __init__(self, db: Session):
        super().__init__(db, Student)

    def get_all_scoped(
        self,
        organization_id: int | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Student]:
        """
        Return all students, optionally filtered by org.
        Pass organization_id=None (super_admin) to get all students across all orgs.
        """
        q = self.db.query(Student)
        if organization_id is not None:
            q = q.filter(Student.organization_id == organization_id)
        return q.order_by(Student.name).offset(skip).limit(limit).all()
    
    def get_by_code(self, code: str) -> Student | None:
        """
        Find a student by their university student code (e.g. "CS2024001").
        Used to check for duplicates before registering a new student.
        """
        return (
            self.db.query(Student)
            .filter(Student.student_code == code)
            .first()
        )

    def get_by_organization(self, org_id: int) -> list[Student]:
        """
        Return all students in a given organization, sorted by name.
        Used to display the student list in the admin UI.
        """
        return (
            self.db.query(Student)
            .filter(Student.organization_id == org_id)
            .order_by(Student.name)
            .all()
        )

    def search_by_name(
        self,
        name: str,
        organization_id: int | None = None,
    ) -> list[Student]:
        """Scoped partial name search — org-filtered for regular admins."""
        q = self.db.query(Student).filter(Student.name.ilike(f"%{name}%"))
        if organization_id is not None:
            q = q.filter(Student.organization_id == organization_id)
        return q.all()

    def get_by_id_scoped(
        self,
        student_id: int,
        organization_id: int | None = None,
    ) -> Student | None:
        """Fetch a single student, enforcing org scope for regular admins."""
        q = self.db.query(Student).filter(Student.id == student_id)
        if organization_id is not None:
            q = q.filter(Student.organization_id == organization_id)
        return q.first()
