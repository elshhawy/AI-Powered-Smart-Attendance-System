# src/api/v1/endpoints/courses.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.core.security import get_current_admin
from src.services.course_service import (
    CourseService,
    CourseNotFoundException,
    CourseAlreadyExistsException,
    CourseSessionNotFoundException,
    InvalidSessionTimeException,
)
from src.schemas.course import (
    CourseCreate,
    CourseUpdate,
    CourseResponse,
    CourseListResponse,
    CourseSessionCreate,
    CourseSessionUpdate,
    CourseSessionResponse,
)

router = APIRouter(prefix="/courses", tags=["Courses"])


# ── Courses ───────────────────────────────────────────────────

@router.post("", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(
    body: CourseCreate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """Create a new course for an organization."""
    try:
        course = CourseService(db).create_course(
            name=body.name,
            code=body.code,
            organization_id=body.organization_id,
            description=body.description,
        )
        return CourseResponse.model_validate(course)
    except CourseAlreadyExistsException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/organization/{org_id}", response_model=CourseListResponse)
def list_courses(
    org_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """List all courses for an organization."""
    courses = CourseService(db).list_courses(org_id)
    return CourseListResponse(
        courses=[CourseResponse.model_validate(c) for c in courses],
        total=len(courses),
    )


@router.get("/{course_id}", response_model=CourseResponse)
def get_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """Get a single course with all its sessions."""
    try:
        course = CourseService(db).get_course(course_id)
        return CourseResponse.model_validate(course)
    except CourseNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{course_id}", response_model=CourseResponse)
def update_course(
    course_id: int,
    body: CourseUpdate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """Update a course (name, code, description, or active status)."""
    try:
        course = CourseService(db).update_course(course_id, body.model_dump())
        return CourseResponse.model_validate(course)
    except CourseNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{course_id}", status_code=status.HTTP_200_OK)
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """Delete a course and all its sessions."""
    try:
        CourseService(db).delete_course(course_id)
        return {"message": f"Course {course_id} deleted successfully."}
    except CourseNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ── Sessions ──────────────────────────────────────────────────

@router.post("/{course_id}/sessions", response_model=CourseSessionResponse, status_code=status.HTTP_201_CREATED)
def add_session(
    course_id: int,
    body: CourseSessionCreate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """Add a new session (lecture/section/lab/etc.) to a course."""
    try:
        session = CourseService(db).add_session(
            course_id=course_id,
            session_type=body.session_type,
            day_of_week=body.day_of_week,
            start_time=body.start_time,
            end_time=body.end_time,
            late_after_minutes=body.late_after_minutes,
        )
        return CourseSessionResponse.model_validate(session)
    except CourseNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidSessionTimeException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{course_id}/sessions", response_model=list[CourseSessionResponse])
def list_sessions(
    course_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """List all sessions for a course."""
    try:
        sessions = CourseService(db).list_sessions(course_id)
        return [CourseSessionResponse.model_validate(s) for s in sessions]
    except CourseNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/sessions/{session_id}", response_model=CourseSessionResponse)
def update_session(
    session_id: int,
    body: CourseSessionUpdate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """Update a session's type, time, day, or late threshold."""
    try:
        session = CourseService(db).update_session(session_id, body.model_dump())
        return CourseSessionResponse.model_validate(session)
    except CourseSessionNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidSessionTimeException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/sessions/{session_id}", status_code=status.HTTP_200_OK)
def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """Delete a session from a course."""
    try:
        CourseService(db).delete_session(session_id)
        return {"message": f"Session {session_id} deleted successfully."}
    except CourseSessionNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/active-session/{org_id}", response_model=CourseSessionResponse | None)
def get_active_session(
    org_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """
    Get the currently active session for an organization.
    Returns null if no session is active right now.
    Used by the camera page to show which class is in session.
    """
    session = CourseService(db).get_active_session_now(org_id)
    if not session:
        return None
    return CourseSessionResponse.model_validate(session)