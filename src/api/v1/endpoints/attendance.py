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
from src.db.repositories.student_repository import StudentRepository
from src.db.repositories.attendance_repository import AttendanceRepository
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
from src.core.security import require_super_admin

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
            detail="Invalid image file.",
        )
    return image


def _assert_org_scope(admin, requested_org_id: int) -> None:
    """Raise 403 if a regular admin tries to access a foreign org."""
    if admin._scoped_org_id is not None and admin._scoped_org_id != requested_org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to this organization's data is not allowed.",
        )


# ── Endpoints ─────────────────────────────────────────────────

@router.post("/process", response_model=AttendanceResponse)
async def process_frame(
    request: Request,
    frame: UploadFile = File(...),
    org_id: int | None = Query(default=None, description="Organization ID for dynamic session detection"),
    db: Session = Depends(get_db),
    api_key: str = Depends(kiosk_key_scheme),
):
    """Kiosk endpoint — authenticated via X-Api-Key, no admin JWT required."""
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

@router.get("/today/all", response_model=AttendanceListResponse)
def get_all_today_attendance(
    request: Request,
    db: Session = Depends(get_db),
    admin=Depends(require_super_admin),
):
    repo = AttendanceRepository(db)
    today = date.today()
    records = repo.get_by_date_range(today, today, org_id=None)
    return AttendanceListResponse(
        records=[AttendanceRecordResponse.model_validate(r) for r in records],
        total=len(records), date_from=today, date_to=today,
    )

@router.get("/today/{organization_id}", response_model=AttendanceListResponse)
def get_today_attendance(
    organization_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    _assert_org_scope(admin, organization_id)
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

@router.get("/range/all", response_model=AttendanceListResponse)
def get_all_attendance_range(
    start_date: date,
    end_date: date,
    request: Request,
    db: Session = Depends(get_db),
    admin=Depends(require_super_admin),
):
    repo = AttendanceRepository(db)
    records = repo.get_by_date_range(start_date, end_date, org_id=None)
    return AttendanceListResponse(
        records=[AttendanceRecordResponse.model_validate(r) for r in records],
        total=len(records), date_from=start_date, date_to=end_date,
    )

@router.get("/range/{organization_id}", response_model=AttendanceListResponse)
def get_attendance_range(
    organization_id: int,
    start_date: date,
    end_date: date,
    request: Request,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    _assert_org_scope(admin, organization_id)
    pipeline = request.app.state.pipeline
    service = AttendanceService(db, pipeline)
    records = service.get_attendance_range(organization_id, start_date, end_date)
    return AttendanceListResponse(
        records=[AttendanceRecordResponse.model_validate(r) for r in records],
        total=len(records),
        date_from=start_date,
        date_to=end_date,
    )

@router.post("/mark-absent/all", response_model=MarkAbsentResponse)
def mark_all_absents(
    request: Request,
    db: Session = Depends(get_db),
    admin=Depends(require_super_admin),
):
    student_repo = StudentRepository(db)
    att_repo = AttendanceRepository(db)
    students = student_repo.get_all()
    today = date.today()
    count = 0
    for s in students:
        if not att_repo.check_duplicate(s.id, today):
            att_repo.mark_absent(s.id, today)
            count += 1
    return MarkAbsentResponse(marked_count=count, date=today, message=f"{count} students marked absent.")    

@router.post("/mark-absent/{organization_id}", response_model=MarkAbsentResponse)
def mark_absents(
    organization_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    _assert_org_scope(admin, organization_id)
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
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """
    Get statistics for a student.
    Regular admins are blocked from accessing students outside their org
    via the scoped query in AttendanceRepository.get_statistics_scoped.
    """
    # First verify the student exists within scope
    student = StudentRepository(db).get_by_id_scoped(
        student_id, organization_id=admin._scoped_org_id
    )
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found.")

    repo = AttendanceRepository(db)
    records = repo.get_statistics_scoped(
        student_id=student_id,
        date_from=start_date,
        date_to=end_date,
        organization_id=admin._scoped_org_id,
    )

    total = len(records)
    present_days = sum(1 for r in records if r.status == "present")
    late_days = sum(1 for r in records if r.is_late)
    percentage = (present_days / total * 100) if total > 0 else 0.0

    return AttendanceStatisticsResponse(
        student_id=student_id,
        attendance_percentage=round(percentage, 2),
        total_days=total,
        present_days=present_days,
        late_days=late_days,
    )