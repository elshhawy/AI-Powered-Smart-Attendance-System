# src/services/student_service.py
import numpy as np
from datetime import date
from sqlalchemy.orm import Session

from src.ai.recognition_pipeline import RecognitionPipeline
from src.db.repositories.student_repository import StudentRepository
from src.core.vector_index import VectorIndex
from src.core.config import settings
from src.models.student import Student


# ── Custom Exceptions ─────────────────────────────────────────────────────────

class StudentAlreadyExistsException(Exception):
    """Raised when trying to enroll a student with a duplicate student_code."""
    pass


class StudentNotFoundException(Exception):
    """Raised when a student is not found in the database."""
    pass


class FaceEnrollmentException(Exception):
    """Raised when face enrollment fails (bad photo, no face, spoof, etc.)."""
    pass


# ── Service ───────────────────────────────────────────────────────────────────

class StudentService:

    def __init__(self, db: Session):
        self.db = db
        self.student_repo = StudentRepository(db)
        self.pipeline = RecognitionPipeline()
        self.index = VectorIndex(
            index_path=settings.FAISS_INDEX_PATH,
            id_map_path=settings.FAISS_ID_MAP_PATH,
        )

    def enroll_student(
        self,
        name: str,
        student_code: str,
        organization_id: int,
        face_image: np.ndarray,
    ) -> Student:
        # Step 1 — Check for duplicate student_code
        existing = self.student_repo.get_by_code(student_code)
        if existing:
            raise StudentAlreadyExistsException(
                f"Student with code '{student_code}' already exists."
            )

        # Step 2 — Extract face embedding
        try:
            embedding = self.pipeline.get_embedding_for_enrollment(face_image)
        except Exception as e:
            raise FaceEnrollmentException(
                f"Failed to extract face from enrollment photo: {e}"
            )

        # Step 3 — Save student to PostgreSQL
        student = self.student_repo.create({
            "name": name,
            "student_code": student_code,
            "organization_id": organization_id,
            "enrollment_date": date.today(),
        })

        # Step 4 — Save embedding to FAISS
        try:
            self.index.add(student_id=student.id, embedding=embedding)
        except Exception as e:
            self.student_repo.delete(student.id)
            raise FaceEnrollmentException(
                f"Failed to save face to index: {e}"
            )

        return student

    def remove_student(self, student_id: int) -> bool:
        student = self.student_repo.get_by_id(student_id)
        if not student:
            raise StudentNotFoundException(
                f"Student with id {student_id} not found."
            )
        self.index.remove(student_id)
        self.student_repo.delete(student_id)
        return True

    def get_student(self, student_id: int) -> Student:
        student = self.student_repo.get_by_id(student_id)
        if not student:
            raise StudentNotFoundException(
                f"Student with id {student_id} not found."
            )
        return student

    def get_student_by_code(self, student_code: str) -> Student:
        student = self.student_repo.get_by_code(student_code)
        if not student:
            raise StudentNotFoundException(
                f"Student with code '{student_code}' not found."
            )
        return student

    def list_students(self, organization_id: int) -> list[Student]:
        return self.student_repo.get_by_organization(organization_id)

    def search_students(self, name_query: str) -> list[Student]:
        return self.student_repo.search_by_name(name_query)

    def get_total_enrolled(self) -> int:
        return self.index.get_total()