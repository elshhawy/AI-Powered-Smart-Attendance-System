# src/db/repositories/base.py
from typing import TypeVar, Generic, Type
from sqlalchemy.orm import Session
from src.db.database import Base

# TypeVar lets us write one BaseRepository that works for any model type.
# When you do AdminRepository(BaseRepository[Admin]),
# Python knows that all methods return Admin objects, not generic objects.
ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Provides five operations for free to any repository that inherits from it:
    get_by_id, get_all, create, update, delete.

    You never call this class directly. You create a subclass:
        class AdminRepository(BaseRepository[Admin]):
            def __init__(self, db): super().__init__(db, Admin)
    """

    def __init__(self, db: Session, model: Type[ModelType]):
        self.db = db        # The database session for this request
        self.model = model  # The SQLAlchemy model class (Admin, Student, etc.)

    def get_by_id(self, id: int) -> ModelType | None:
        """
        Find one row by its primary key.
        Returns None if no row with that id exists.
        """
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> list[ModelType]:
        """
        Return all rows, with optional pagination.
        skip=0, limit=100 means: return the first 100 rows.
        skip=100, limit=100 means: return rows 101-200.
        """
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def create(self, obj_in: dict) -> ModelType:
        """
        Insert a new row.
        obj_in is a dict like {"email": "a@b.com", "hashed_password": "..."}

        After commit(), we call refresh() to reload the object from the database.
        This fills in the auto-generated id and any default values
        (like created_at = datetime.utcnow) that PostgreSQL set.
        Without refresh(), the object would still show id=None.
        """
        db_obj = self.model(**obj_in)   # Create the Python object
        self.db.add(db_obj)             # Tell SQLAlchemy to track it
        self.db.commit()                # Write to the database
        self.db.refresh(db_obj)         # Reload from DB to get generated values
        return db_obj

    def update(self, db_obj: ModelType, data: dict) -> ModelType:
        """
        Update an existing row.
        db_obj is the object you already loaded. data is the fields to change.
        Example: update(admin, {"full_name": "New Name"})
        """
        for field, value in data.items():
            setattr(db_obj, field, value)   # Set each attribute on the object
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, id: int) -> bool:
        """
        Delete a row by id.
        Returns True if deleted, False if not found.
        """
        obj = self.get_by_id(id)
        if not obj:
            return False
        self.db.delete(obj)
        self.db.commit()
        return True