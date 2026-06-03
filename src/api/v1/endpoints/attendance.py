# src/api/v1/endpoints/attendance.py
import cv2
import numpy as np
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Request, Query
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

kiosk_key_scheme = APIKeyHeader(name="X-Api-Key", auto_error=False)


# ── Helper ────────────────────────────────────────────────────

async def read_image_file(file: UploadFile) -> np.ndarray:
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image file."
        )
    return image


# ── Endpoints ─────────────────────────────────────────────────

@router.post("/process", response_model=AttendanceResponse)
async def process_frame(
    request: Request,
    frame: UploadFile = File(...),
    org_id: int | None = Query(default=None, description="Organization ID for dynamic session detection"),
    db: Session = Depends(get_db),
    api_key: str = Depends(kiosk_key_scheme),
):
    """
    Process a camera frame and record attendance.

    - Authenticated via X-Api-Key header (kiosk device)
    - If org_id is provided: automatically detects the active course session
      and uses its late threshold dynamically
    - If no org_id or no active session: falls back to .env settings
    """
    if not api_key or api_key != settings.KIOSK_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing kiosk API key",
        )

    pipeline = request.app.state.pipeline
    image = await read_image_file(frame)
    service = AttendanceService(db, pipeline)

    try:
        record = service.process_frame(image, org_id=org_id)

        if record.already_marked:
            message = f"Already marked! Welcome back, {record.student_name}."
        elif record.is_late:
            message = f"You are late, {record.student_name}."
        else:
            message = f"Welcome, {record.student_name}! Attendance recorded."

        # Append course/session info to message if available
        if record.course_name and record.session_type:
            message += f" ({record.course_name} — {record.session_type})"

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
    request: Request,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    pipeline = request.app.state.pipeline
    service = AttendanceService(db, pipeline)
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
    request: Request,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    pipeline = request.app.state.pipeline
    service = AttendanceService(db, pipeline)
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
    request: Request,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    pipeline = request.app.state.pipeline
    service = AttendanceService(db, pipeline)
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
    request: Request,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    pipeline = request.app.state.pipeline
    service = AttendanceService(db, pipeline)
    stats = service.get_student_statistics(student_id, start_date, end_date)
    return AttendanceStatisticsResponse(student_id=student_id, **stats)