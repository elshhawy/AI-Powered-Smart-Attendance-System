# src/api/v1/endpoints/students.py
import cv2
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Request
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.core.security import get_current_admin
from src.services.student_service import (
    StudentService,
    StudentAlreadyExistsException,
    StudentNotFoundException,
    FaceEnrollmentException,
)
from src.schemas.student import (
    StudentResponse,
    StudentListResponse,
    EnrollmentResponse,
)

router = APIRouter(prefix="/students", tags=["Students"])


# ── Helper ────────────────────────────────────────────────────────────────────

async def read_image_file(file: UploadFile) -> np.ndarray:
    """Convert an uploaded image file to a numpy array (OpenCV BGR format)."""
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image file. Please upload a valid JPG or PNG."
        )
    return image


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/enroll", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED)
async def enroll_student(
    request: Request,
    name: str = Form(...),
    student_code: str = Form(...),
    organization_id: int = Form(...),
    face_photo: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """
    Register a new student and their face in the system.

    - Requires admin authentication (JWT token)
    - Accepts multipart/form-data (text fields + image file)
    - The face photo must contain exactly one clear face
    """
    image = await read_image_file(face_photo)
    # Get the shared pipeline from app.state — loaded once at startup in main.py
    pipeline = request.app.state.pipeline
    service = StudentService(db, pipeline)

    try:
        student = service.enroll_student(
            name=name,
            student_code=student_code,
            organization_id=organization_id,
            face_image=image,
        )
        return EnrollmentResponse(
            student=StudentResponse.model_validate(student),
            faces_in_index=service.get_total_enrolled(),
        )

    except StudentAlreadyExistsException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except FaceEnrollmentException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{student_id}", status_code=status.HTTP_200_OK)
def remove_student(
    student_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """Remove a student from the system (PostgreSQL + FAISS). Requires admin authentication."""
    pipeline = request.app.state.pipeline
    service = StudentService(db, pipeline)

    try:
        service.remove_student(student_id)
        return {"message": f"Student {student_id} removed successfully."}
    except StudentNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/organization/{organization_id}", response_model=StudentListResponse)
def list_students(
    organization_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """List all students in an organization. Requires admin authentication."""
    pipeline = request.app.state.pipeline
    service = StudentService(db, pipeline)
    students = service.list_students(organization_id)

    return StudentListResponse(
        students=[StudentResponse.model_validate(s) for s in students],
        total=len(students),
    )


@router.get("/{student_id}", response_model=StudentResponse)
def get_student(
    student_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """Get a single student by ID. Requires admin authentication."""
    pipeline = request.app.state.pipeline
    service = StudentService(db, pipeline)

    try:
        student = service.get_student(student_id)
        return StudentResponse.model_validate(student)
    except StudentNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/search/{query}", response_model=StudentListResponse)
def search_students(
    query: str,
    request: Request,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """Search students by name (partial match). Requires admin authentication."""
    pipeline = request.app.state.pipeline
    service = StudentService(db, pipeline)
    students = service.search_students(query)

    return StudentListResponse(
        students=[StudentResponse.model_validate(s) for s in students],
        total=len(students),
    )