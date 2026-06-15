# src/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import JWTError

from src.db.database import get_db
from src.db.repositories.user_repository import UserRepository
from src.db.repositories.admin_repository import AdminRepository
from src.core.security import (
    verify_password,
    hash_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    get_current_user,
    require_admin,
)
from src.schemas.user import (
    SignUpRequest,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UserResponse,
    LinkStudentRequest,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

DUMMY_HASH = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewohPNk2GL5tF3se"


# ── Sign Up ───────────────────────────────────────────────────

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(body: SignUpRequest, db: Session = Depends(get_db)):
    """
    Register a new user (admin or student).

    - role = "admin"   → can manage students, courses, attendance
    - role = "student" → can only view their own attendance

    Note: after signup, an existing admin must link the student account
    to a student record using POST /auth/link-student
    """
    repo = UserRepository(db)

    if repo.email_exists(body.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    if len(body.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters",
        )

    if body.role not in ("admin", "student"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be 'admin' or 'student'",
        )

    user = repo.create({
        "email":           body.email,
        "hashed_password": hash_password(body.password),
        "full_name":       body.full_name,
        "role":            body.role,
        "is_active":       True,
        "student_id":      None,
    })

    return UserResponse.model_validate(user)


# ── Login ─────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """
    Login with email + password.
    Works for both admins and students.
    Returns JWT tokens with role embedded.
    """
    repo = UserRepository(db)
    user = repo.get_by_email(body.email)

    password_to_check = user.hashed_password if (user and user.hashed_password) else DUMMY_HASH

    if not user or not verify_password(body.password, password_to_check):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is deactivated",
        )

    # Google-only users have no password
    if not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account uses Google Sign-In. Please sign in with Google.",
        )

    return TokenResponse(
        access_token=  create_access_token(user.id, user.role, user.student_id),
        refresh_token= create_refresh_token(user.id, user.role),
        token_type=    "bearer",
        user_name=     user.full_name,
        role=          user.role,
        student_id=    user.student_id,
    )


# ── Refresh ───────────────────────────────────────────────────

@router.post("/refresh")
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    """Exchange refresh token for new access token."""
    try:
        payload = verify_token(body.refresh_token, "refresh")
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user = UserRepository(db).get_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or deactivated")

    return {
        "access_token": create_access_token(user.id, user.role, user.student_id),
        "token_type":   "bearer",
        "role":         user.role,
    }


# ── Me ────────────────────────────────────────────────────────

@router.get("/me", response_model=UserResponse)
def get_me(user=Depends(get_current_user)):
    """Get current user info — works for admin and student."""
    return UserResponse.model_validate(user)


# ── Link Student ──────────────────────────────────────────────

@router.post("/link-student", response_model=UserResponse)
def link_student(
    body: LinkStudentRequest,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """
    Admin links a user account to a student record.
    After this, the student can login and see their own attendance.
    """
    repo = UserRepository(db)
    user = repo.get_by_id(body.user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role != "student":
        raise HTTPException(status_code=400, detail="User is not a student")

    # Check student exists
    from src.db.repositories.student_repository import StudentRepository
    student = StudentRepository(db).get_by_id(body.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student record not found")

    updated = repo.update(user, {"student_id": body.student_id})
    return UserResponse.model_validate(updated)


# ── List Users (Admin only) ───────────────────────────────────

@router.get("/users", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """List all registered users. Admin only."""
    users = UserRepository(db).get_all()
    return [UserResponse.model_validate(u) for u in users]