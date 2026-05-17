# src/schemas/student.py
from datetime import date
from pydantic import BaseModel, Field


# ── Request Schemas ───────────────────────────────────────────────────────────

class StudentEnrollRequest(BaseModel):
    """
    Sent by the admin when registering a new student.
    The face photo is sent separately as a file upload (not in this schema).
    """
    name: str = Field(..., min_length=2, max_length=100, example="Ahmed Mohamed")
    student_code: str = Field(..., min_length=1, max_length=50, example="20210001")
    organization_id: int = Field(..., gt=0, example=1)


class StudentSearchRequest(BaseModel):
    """Used for searching students by name."""
    query: str = Field(..., min_length=1, max_length=100, example="Ahmed")


# ── Response Schemas ──────────────────────────────────────────────────────────

class StudentResponse(BaseModel):
    """
    Returned after creating or fetching a student.
    Never includes face embeddings — those stay in FAISS only.
    """
    id: int
    name: str
    student_code: str
    organization_id: int
    enrollment_date: date

    model_config = {"from_attributes": True}  # ✅ Pydantic v2 style


class StudentListResponse(BaseModel):
    """Returned when listing all students in an organization."""
    students: list[StudentResponse]
    total: int


class EnrollmentResponse(BaseModel):
    """Returned after successfully enrolling a student."""
    student: StudentResponse
    message: str = "Student enrolled successfully"
    faces_in_index: int