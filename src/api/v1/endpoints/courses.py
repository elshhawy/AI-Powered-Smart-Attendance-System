# src/api/v1/endpoints/courses.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.core.security import get_current_admin
from src.db.repositories.course_repository import CourseRepository
from src.db.repositories.course_session_repository import CourseSessionRepository
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
from src.core.security import require_super_admin

router = APIRouter(prefix="/courses", tags=["Courses"])


# ── Internal helpers ──────────────────────────────────────────

def _resolve_org(admin, requested_org_id: int | None = None) -> int | None:
    """
    For path params that carry an org_id, verify the admin is allowed to access it.
    Returns the effective org_id to use in queries, or raises 403.
    """
    if admin._scoped_org_id is None:
        # super_admin: accept whatever org was requested (or None = all)
        return requested_org_id
    if requested_org_id is not None and requested_org_id != admin._scoped_org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to this organization's data is not allowed.",
        )
    return admin._scoped_org_id


def _assert_course_owned(course_id: int, admin, db: Session) -> None:
    """Raise 404 if course doesn't exist or 403 if it belongs to a foreign org."""
    repo = CourseRepository(db)
    course = repo.get_by_id_scoped(course_id, organization_id=admin._scoped_org_id)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Course {course_id} not found.")


# ── Courses ───────────────────────────────────────────────────

@router.post("", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(
    body: CourseCreate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Create a new course. Regular admin can only create within their own org."""
    _resolve_org(admin, body.organization_id)  # raises 403 if foreign org
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


@router.get("/", response_model=CourseListResponse)
def list_all_courses(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """List courses scoped to admin's org; super_admin gets all."""
    repo = CourseRepository(db)
    courses = repo.get_all_scoped(organization_id=admin._scoped_org_id)
    return CourseListResponse(
        courses=[CourseResponse.model_validate(c) for c in courses],
        total=len(courses),
    )


@router.get("/organization/{org_id}", response_model=CourseListResponse)
def list_courses_by_org(
    org_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """List courses for a specific org, with scope enforcement."""
    _resolve_org(admin, org_id)
    courses = CourseService(db).list_courses(org_id)
    return CourseListResponse(
        courses=[CourseResponse.model_validate(c) for c in courses],
        total=len(courses),
    )

@router.get("/active-session/all", response_model=CourseSessionResponse | None)
def get_all_active_session(db: Session = Depends(get_db), admin=Depends(require_super_admin)):
    """Super admins view all orgs, so there is no single 'active' session to return."""
    return None    

@router.get("/active-session/{org_id}", response_model=CourseSessionResponse | None)
def get_active_session(
    org_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Get the currently active session for an org. Scope-enforced."""
    _resolve_org(admin, org_id)
    session = CourseService(db).get_active_session_now(org_id)
    if not session:
        return None
    return CourseSessionResponse.model_validate(session)


@router.get("/{course_id}", response_model=CourseResponse)
def get_course(
    course_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Get a single course. Returns 404 if outside admin's org scope."""
    repo = CourseRepository(db)
    course = repo.get_by_id_scoped(course_id, organization_id=admin._scoped_org_id)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Course {course_id} not found.")
    return CourseResponse.model_validate(course)


@router.put("/{course_id}", response_model=CourseResponse)
def update_course(
    course_id: int,
    body: CourseUpdate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Update a course. Scope-checked before mutation."""
    _assert_course_owned(course_id, admin, db)
    try:
        course = CourseService(db).update_course(course_id, body.model_dump())
        return CourseResponse.model_validate(course)
    except CourseNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{course_id}", status_code=status.HTTP_200_OK)
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Delete a course. Scope-checked before deletion."""
    _assert_course_owned(course_id, admin, db)
    try:
        CourseService(db).delete_course(course_id)
        return {"message": f"Course {course_id} deleted successfully."}
    except CourseNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ── Sessions ──────────────────────────────────────────────────

def _assert_session_owned(session_id: int, admin, db: Session) -> None:
    """Verify a session's parent course belongs to the admin's org."""
    from src.models.course import Course
    from src.models.course_session import CourseSession

    q = (
        db.query(CourseSession)
        .join(Course, CourseSession.course_id == Course.id)
        .filter(CourseSession.id == session_id)
    )
    if admin._scoped_org_id is not None:
        q = q.filter(Course.organization_id == admin._scoped_org_id)
    session = q.first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found.")


@router.post("/{course_id}/sessions", response_model=CourseSessionResponse, status_code=status.HTTP_201_CREATED)
def add_session(
    course_id: int,
    body: CourseSessionCreate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Add a session to a course. Scope-checked."""
    _assert_course_owned(course_id, admin, db)
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
    admin=Depends(get_current_admin),
):
    """List sessions for a course. Scope-checked."""
    _assert_course_owned(course_id, admin, db)
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
    admin=Depends(get_current_admin),
):
    """Update a session. Verifies session belongs to admin's org."""
    _assert_session_owned(session_id, admin, db)
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
    admin=Depends(get_current_admin),
):
    """Delete a session. Verifies session belongs to admin's org."""
    _assert_session_owned(session_id, admin, db)
    try:
        CourseService(db).delete_session(session_id)
        return {"message": f"Session {session_id} deleted successfully."}
    except CourseSessionNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
