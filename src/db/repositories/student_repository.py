# src/db/repositories/student_repository.py
from sqlalchemy.orm import Session
from src.models.student import Student
from src.db.repositories.base import BaseRepository


class StudentRepository(BaseRepository[Student]):

    def __init__(self, db: Session):
        super().__init__(db, Student)

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

    def search_by_name(self, name: str) -> list[Student]:
        """
        Case-insensitive partial name search.
        ilike means "case-insensitive LIKE".
        The % signs mean "any characters before and after".
        search_by_name("ahmed") matches "Ahmed Khaled", "Mohamed Ahmed", etc.
        """
        return (
            self.db.query(Student)
            .filter(Student.name.ilike(f"%{name}%"))
            .all()
        )