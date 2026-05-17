# src/db/repositories/admin_repository.py
from sqlalchemy.orm import Session
from src.models.admin import Admin
from src.db.repositories.base import BaseRepository


class AdminRepository(BaseRepository[Admin]):

    def __init__(self, db: Session):
        # Call the parent __init__ and tell it we work with the Admin model
        super().__init__(db, Admin)

    def get_by_email(self, email: str) -> Admin | None:
        """
        Used by the login endpoint to find an admin by their email address.
        Returns None if no admin with that email exists.

        Why do we need this separately from get_by_id?
        Because the login flow only has the email, not the id.
        The admin types their email → we find them → we verify their password.
        """
        return (
            self.db.query(Admin)
            .filter(Admin.email == email)
            .first()
        )

    def get_active(self) -> list[Admin]:
        """Return all admin accounts that are not deactivated."""
        return (
            self.db.query(Admin)
            .filter(Admin.is_active == True)
            .all()
        )