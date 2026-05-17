# src/schemas/attendance.py
from datetime import date, datetime
from pydantic import BaseModel


# ── Response Schemas ──────────────────────────────────────────────────────────

class AttendanceResponse(BaseModel):
    """
    Returned after processing a camera frame.
    Shown on the kiosk screen to confirm the student's attendance.
    """
    student_id: int
    student_name: str
    is_late: bool
    confidence: float
    already_marked: bool
    message: str  # e.g. "Welcome Ahmed!" or "You are late!"

    class Config:
        from_attributes = True


class AttendanceRecordResponse(BaseModel):
    """
    Single attendance record — used in reports and dashboard.

    Note: student_name is NOT a column in the Attendance model.
    It comes from the relationship: record.student.name
    We use a validator to handle this via from_attributes = True
    and the SQLAlchemy relationship loading it automatically.
    """
    id: int
    student_id: int
    date: date
    timestamp: datetime | None
    status: str        # "present" or "absent"
    is_late: bool
    confidence: float | None

    class Config:
        from_attributes = True  # allows converting SQLAlchemy model to this schema


class AttendanceListResponse(BaseModel):
    """Returned when fetching attendance for a date range."""
    records: list[AttendanceRecordResponse]
    total: int
    date_from: date
    date_to: date


class AttendanceStatisticsResponse(BaseModel):
    """Returned when fetching statistics for a single student."""
    student_id: int
    attendance_percentage: float
    total_days: int
    present_days: int
    late_days: int


class MarkAbsentResponse(BaseModel):
    """Returned after marking all absent students."""
    marked_count: int
    date: date
    message: str