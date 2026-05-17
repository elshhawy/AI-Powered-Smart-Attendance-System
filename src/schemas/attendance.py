# src/schemas/attendance.py
from datetime import date, datetime
from pydantic import BaseModel, Field


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
    """Single attendance record — used in reports and dashboard."""
    id: int
    student_id: int
    student_name: str
    date: date
    timestamp: datetime
    status: str       # "present" or "absent"
    is_late: bool
    confidence: float | None

    class Config:
        from_attributes = True


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