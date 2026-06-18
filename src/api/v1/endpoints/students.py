# src/api/v1/endpoints/students.py
import cv2
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Request
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.core.security import get_current_admin
from src.db.repositories.student_repository import StudentRepository
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
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image file. Please upload a valid JPG or PNG.",
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
    admin=Depends(get_current_admin),
):
    """Register a new student. Regular admins can only enroll into their own org."""
    # Enforce: regular admin cannot enroll into a foreign org
    if admin._scoped_org_id is not None and admin._scoped_org_id != organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only enroll students into your own organization.",
        )

    image = await read_image_file(face_photo)
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


@router.get("/", response_model=StudentListResponse)
def list_all_students(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """
    List students scoped to the admin's org.
    super_admin receives all students across all orgs.
    """
    repo = StudentRepository(db)
    students = repo.get_all_scoped(organization_id=admin._scoped_org_id)
    return StudentListResponse(
        students=[StudentResponse.model_validate(s) for s in students],
        total=len(students),
    )


@router.get("/organization/{organization_id}", response_model=StudentListResponse)
def list_students_by_org(
    organization_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """List students in a specific org. Regular admin is blocked if org doesn't match."""
    if admin._scoped_org_id is not None and admin._scoped_org_id != organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to this organization's data is not allowed.",
        )
    repo = StudentRepository(db)
    students = repo.get_by_organization(organization_id)
    return StudentListResponse(
        students=[StudentResponse.model_validate(s) for s in students],
        total=len(students),
    )


@router.get("/search/{query}", response_model=StudentListResponse)
def search_students(
    query: str,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Search students by name, scoped to admin's org."""
    repo = StudentRepository(db)
    students = repo.search_by_name(query, organization_id=admin._scoped_org_id)
    return StudentListResponse(
        students=[StudentResponse.model_validate(s) for s in students],
        total=len(students),
    )


@router.get("/{student_id}", response_model=StudentResponse)
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Fetch one student, enforcing org scope."""
    repo = StudentRepository(db)
    student = repo.get_by_id_scoped(student_id, organization_id=admin._scoped_org_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found.")
    return StudentResponse.model_validate(student)


@router.delete("/{student_id}", status_code=status.HTTP_200_OK)
def remove_student(
    student_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Remove a student. Regular admin is blocked from deleting outside their org."""
    # Verify ownership before deletion
    repo = StudentRepository(db)
    student = repo.get_by_id_scoped(student_id, organization_id=admin._scoped_org_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found.")

    pipeline = request.app.state.pipeline
    service = StudentService(db, pipeline)
    try:
        service.remove_student(student_id)
        return {"message": f"Student {student_id} removed successfully."}
    except StudentNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))