# src/db/repositories/user_repository.py
from sqlalchemy.orm import Session
from src.models.user import User
from src.db.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):

    def __init__(self, db: Session):
        super().__init__(db, User)

    def get_by_email(self, email: str) -> User | None:
        """Find user by email — used in login."""
        return (
            self.db.query(User)
            .filter(User.email == email)
            .first()
        )

    def get_by_google_id(self, google_id: str) -> User | None:
        """Find user by Google ID — used in Google OAuth."""
        return (
            self.db.query(User)
            .filter(User.google_id == google_id)
            .first()
        )

    def get_by_student_id(self, student_id: int) -> User | None:
        """Find the user account linked to a student."""
        return (
            self.db.query(User)
            .filter(User.student_id == student_id)
            .first()
        )

    def get_admins(self) -> list[User]:
        """All admin users."""
        return (
            self.db.query(User)
            .filter(User.role == "admin", User.is_active == True)
            .all()
        )

    def get_students(self) -> list[User]:
        """All student users."""
        return (
            self.db.query(User)
            .filter(User.role == "student", User.is_active == True)
            .all()
        )

    def email_exists(self, email: str) -> bool:
        """Check if email is already registered."""
        return self.get_by_email(email) is not None
    
    def get_all_scoped(self, organization_id: int | None = None) -> list[User]:
        """Admins + students visible to this org. None (super_admin) = everyone."""
        if organization_id is None:
            return self.db.query(User).all()
        from src.models.student import Student
        return (
            self.db.query(User)
            .outerjoin(Student, User.student_id == Student.id)
            .filter(
                ((User.role == "admin") & (User.organization_id == organization_id))
                | ((User.role == "student") & (Student.organization_id == organization_id))
            )
            .all()
        )