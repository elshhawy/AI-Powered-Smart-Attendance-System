# src/api/v1/endpoints/attendance.py
import cv2
import numpy as np
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.core.security import get_current_admin
from src.core.config import settings
from src.services.attendance_service import (
    AttendanceService,
    UnknownFaceException,
    SpoofDetectedException,
)
from src.schemas.attendance import (
    AttendanceResponse,
    AttendanceListResponse,
    AttendanceRecordResponse,
    AttendanceStatisticsResponse,
    MarkAbsentResponse,
)

router = APIRouter(prefix="/attendance", tags=["Attendance"])

# Kiosk API key scheme — shows a lock icon in Swagger UI
kiosk_key_scheme = APIKeyHeader(name="X-Api-Key", auto_error=False)


# ── Helper ────────────────────────────────────────────────────────────────────

async def read_image_file(file: UploadFile) -> np.ndarray:
    """Convert uploaded image to OpenCV BGR numpy array."""
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image file."
        )
    return image


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/process", response_model=AttendanceResponse)
async def process_frame(
    frame: UploadFile = File(...),
    db: Session = Depends(get_db),
    api_key: str = Depends(kiosk_key_scheme),
):
    """
    Process a camera frame and record attendance if a student is recognised.

    - Called by the kiosk (camera device), NOT the admin
    - Authenticates using X-Api-Key header (KIOSK_API_KEY from .env)
    - Returns student name and attendance status for display on kiosk screen
    """
    # Verify kiosk key
    if not api_key or api_key != settings.KIOSK_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing kiosk API key",
        )

    image = await read_image_file(frame)
    service = AttendanceService(db)

    try:
        record = service.process_frame(image)

        if record.already_marked:
            message = f"Already marked! Welcome back, {record.student_name}."
        elif record.is_late:
            message = f"You are late, {record.student_name}. Please see your instructor."
        else:
            message = f"Welcome, {record.student_name}! Attendance recorded."

        return AttendanceResponse(
            student_id=record.student_id,
            student_name=record.student_name,
            is_late=record.is_late,
            confidence=record.confidence,
            already_marked=record.already_marked,
            message=message,
        )

    except SpoofDetectedException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    except UnknownFaceException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/today/{organization_id}", response_model=AttendanceListResponse)
def get_today_attendance(
    organization_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """
    Get today's attendance for an organization.
    Requires admin authentication.
    """
    service = AttendanceService(db)
    records = service.get_today_attendance(organization_id)
    today = date.today()

    return AttendanceListResponse(
        records=[AttendanceRecordResponse.model_validate(r) for r in records],
        total=len(records),
        date_from=today,
        date_to=today,
    )


@router.get("/range/{organization_id}", response_model=AttendanceListResponse)
def get_attendance_range(
    organization_id: int,
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """
    Get attendance for a date range.
    Requires admin authentication.
    """
    service = AttendanceService(db)
    records = service.get_attendance_range(organization_id, start_date, end_date)

    return AttendanceListResponse(
        records=[AttendanceRecordResponse.model_validate(r) for r in records],
        total=len(records),
        date_from=start_date,
        date_to=end_date,
    )


@router.post("/mark-absent/{organization_id}", response_model=MarkAbsentResponse)
def mark_absents(
    organization_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """
    Mark all students who haven't checked in today as absent.
    Requires admin authentication.
    """
    service = AttendanceService(db)
    count = service.mark_absents(organization_id)

    return MarkAbsentResponse(
        marked_count=count,
        date=date.today(),
        message=f"{count} students marked as absent for today.",
    )


@router.get("/statistics/{student_id}", response_model=AttendanceStatisticsResponse)
def get_student_statistics(
    student_id: int,
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """
    Get attendance statistics for a single student.
    Requires admin authentication.
    """
    service = AttendanceService(db)
    stats = service.get_student_statistics(student_id, start_date, end_date)

    return AttendanceStatisticsResponse(
        student_id=student_id,
        **stats,
    )