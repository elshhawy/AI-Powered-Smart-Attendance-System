# src/api/v1/endpoints/student_portal.py
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.db.database import get_db
from src.core.security import require_student
from src.db.repositories.attendance_repository import AttendanceRepository
from src.db.repositories.student_repository import StudentRepository
from src.db.repositories.course_session_repository import CourseSessionRepository
from src.db.repositories.course_repository import CourseRepository
from src.llm.context_builder import ContextBuilder
from src.llm.prompts import build_student_prompt
from src.llm.rag_pipeline import RAGPipeline

router = APIRouter(prefix="/student", tags=["Student Portal"])


# ── Response Schemas ──────────────────────────────────────────

class StudentProfileResponse(BaseModel):
    student_id: int
    name: str
    student_code: str
    organization_id: int
    enrollment_date: date
    attendance_percentage: float
    total_days: int
    present_days: int
    late_days: int
    absent_days: int

    model_config = {"from_attributes": True}


class AttendanceRecordResponse(BaseModel):
    id: int
    date: date
    status: str
    is_late: bool
    confidence: float | None
    course_name: str | None = None
    session_type: str | None = None

    model_config = {"from_attributes": True}


class ScheduleResponse(BaseModel):
    course_name: str
    course_code: str
    session_type: str
    day_of_week: int
    day_name: str
    start_time: str
    end_time: str
    late_after_minutes: int


DAY_NAMES = {
    0: "Monday", 1: "Tuesday", 2: "Wednesday",
    3: "Thursday", 4: "Friday", 5: "Saturday", 6: "Sunday"
}


# ── Endpoints ─────────────────────────────────────────────────

@router.get("/me", response_model=StudentProfileResponse)
def get_my_profile(
    db: Session = Depends(get_db),
    user=Depends(require_student),
):
    """
    Get the student's profile with overall attendance statistics.
    Only accessible by the logged-in student.
    """
    if not user.student_id:
        raise HTTPException(
            status_code=400,
            detail="Your account is not linked to a student record yet. Please contact your admin.",
        )

    student = StudentRepository(db).get_by_id(user.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student record not found")

    # Calculate overall attendance stats
    all_records = AttendanceRepository(db).get_by_student(user.student_id)
    total       = len(all_records)
    present     = sum(1 for r in all_records if r.status == "present" and not r.is_late)
    late        = sum(1 for r in all_records if r.is_late)
    absent      = sum(1 for r in all_records if r.status == "absent")
    percentage  = round(((present + late) / total * 100) if total else 0, 2)

    return StudentProfileResponse(
        student_id=           student.id,
        name=                 student.name,
        student_code=         student.student_code,
        organization_id=      student.organization_id,
        enrollment_date=      student.enrollment_date,
        attendance_percentage=percentage,
        total_days=           total,
        present_days=         present,
        late_days=            late,
        absent_days=          absent,
    )


@router.get("/attendance", response_model=list[AttendanceRecordResponse])
def get_my_attendance(
    days: int = 30,
    db: Session = Depends(get_db),
    user=Depends(require_student),
):
    """
    Get the student's attendance records for the last N days.
    Default: last 30 days.
    """
    if not user.student_id:
        raise HTTPException(status_code=400, detail="Account not linked to student record")

    end_date   = date.today()
    start_date = end_date - timedelta(days=days)

    records = AttendanceRepository(db).get_by_date_range(
        date_from=start_date,
        date_to=end_date,
    )

    # Filter for this student only
    my_records = [r for r in records if r.student_id == user.student_id]

    result = []
    for r in my_records:
        course_name  = None
        session_type = None
        if r.course_session_id and r.course_session:
            course_name  = r.course_session.course.name
            session_type = r.course_session.session_type

        result.append(AttendanceRecordResponse(
            id=           r.id,
            date=         r.date,
            status=       r.status,
            is_late=      r.is_late,
            confidence=   r.confidence,
            course_name=  course_name,
            session_type= session_type,
        ))

    return result


@router.get("/schedule", response_model=list[ScheduleResponse])
def get_my_schedule(
    db: Session = Depends(get_db),
    user=Depends(require_student),
):
    """
    Get the student's weekly schedule (all active course sessions
    for their organization).
    """
    if not user.student_id:
        raise HTTPException(status_code=400, detail="Account not linked to student record")

    student = StudentRepository(db).get_by_id(user.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student record not found")

    # Get all active courses in this student's organization
    courses = CourseRepository(db).get_active_by_organization(student.organization_id)

    schedule = []
    for course in courses:
        sessions = CourseSessionRepository(db).get_by_course(course.id)
        for session in sessions:
            if not session.is_active:
                continue
            schedule.append(ScheduleResponse(
                course_name=        course.name,
                course_code=        course.code,
                session_type=       session.session_type,
                day_of_week=        session.day_of_week,
                day_name=           DAY_NAMES[session.day_of_week],
                start_time=         str(session.start_time)[:5],
                end_time=           str(session.end_time)[:5],
                late_after_minutes= session.late_after_minutes,
            ))

    # Sort by day of week then start time
    schedule.sort(key=lambda x: (x.day_of_week, x.start_time))
    return schedule


@router.get("/statistics")
def get_my_statistics(
    days: int = 30,
    db: Session = Depends(get_db),
    user=Depends(require_student),
):
    """
    Get detailed attendance statistics for the student.
    Breakdown by course and session type.
    """
    if not user.student_id:
        raise HTTPException(status_code=400, detail="Account not linked to student record")

    end_date   = date.today()
    start_date = end_date - timedelta(days=days)

    records = AttendanceRepository(db).get_by_date_range(
        date_from=start_date,
        date_to=end_date,
    )
    my_records = [r for r in records if r.student_id == user.student_id]

    total   = len(my_records)
    present = sum(1 for r in my_records if r.status == "present" and not r.is_late)
    late    = sum(1 for r in my_records if r.is_late)
    absent  = sum(1 for r in my_records if r.status == "absent")

    # Breakdown by course
    course_stats: dict[str, dict] = {}
    for r in my_records:
        course_name = "Unknown"
        if r.course_session_id and r.course_session:
            course_name = r.course_session.course.name

        if course_name not in course_stats:
            course_stats[course_name] = {"present": 0, "late": 0, "absent": 0, "total": 0}

        course_stats[course_name]["total"] += 1
        if r.status == "absent":
            course_stats[course_name]["absent"] += 1
        elif r.is_late:
            course_stats[course_name]["late"] += 1
        else:
            course_stats[course_name]["present"] += 1

    return {
        "period_days":            days,
        "total_records":          total,
        "present_days":           present,
        "late_days":              late,
        "absent_days":            absent,
        "attendance_percentage":  round(((present + late) / total * 100) if total else 0, 2),
        "at_risk":                ((present + late) / total * 100 if total else 0) < 75,
        "by_course":              course_stats,
    }


# ── Chatbot ───────────────────────────────────────────────────

class StudentChatMessage(BaseModel):
    role: str     # "user" or "assistant"
    content: str


class StudentChatRequest(BaseModel):
    message: str
    history: list[StudentChatMessage] = []


class StudentChatResponse(BaseModel):
    reply: str


@router.post("/chat", response_model=StudentChatResponse)
def student_chat(
    body: StudentChatRequest,
    db: Session = Depends(get_db),
    user=Depends(require_student),
):
    """
    Send a message to the AI assistant, scoped to the student's own
    attendance data only. The student cannot see or ask about other
    students through this endpoint.
    """
    if not user.student_id:
        raise HTTPException(status_code=400, detail="Account not linked to student record")

    try:
        builder = ContextBuilder(db)
        context = builder.build_student_context(user.student_id)

        history = [{"role": msg.role, "content": msg.content} for msg in body.history]

        pipeline = RAGPipeline()
        system_prompt = build_student_prompt(context)

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history[-10:])
        messages.append({"role": "user", "content": body.message})

        response = pipeline.client.chat.completions.create(
            model=pipeline.MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=1024,
        )

        return StudentChatResponse(reply=response.choices[0].message.content)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chatbot error: {str(e)}")