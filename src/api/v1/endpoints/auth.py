# src/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import JWTError

from src.db.database import get_db
from src.db.repositories.user_repository import UserRepository
from src.models.organization import Organization
from src.core.security import (
    verify_password,
    hash_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    get_current_user,
    get_current_admin,
    require_admin,
    require_super_admin,    
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


# ── Sign Up (students only) ─────────────────────────────────

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(body: SignUpRequest, db: Session = Depends(get_db)):
    """
    Public registration — STUDENTS ONLY.
    Requires a valid `student_code` that already exists in the students table;
    the account is auto-bound to that student record on creation.
    Admin/super_admin accounts cannot be self-registered.
    """
    if body.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Public signup is for students only. Admin accounts are created by a super_admin.",
        )

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

    if not body.student_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="student_code is required for student signup",
        )

    from src.db.repositories.student_repository import StudentRepository
    student = StudentRepository(db).get_by_code(body.student_code)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid student_code: no matching student record",
        )

    if repo.get_by_student_id(student.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This student record is already linked to an account",
        )

    user = repo.create({
        "email":           body.email,
        "hashed_password": hash_password(body.password),
        "full_name":       body.full_name,
        "role":            "student",
        "is_active":       True,
        "student_id":      student.id,
        "organization_id": None,
    })

    return UserResponse.model_validate(user)


# ── Admin Creation (super_admin only) ───────────────────────

@router.post("/admins", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_admin(
    body: SignUpRequest,
    db: Session = Depends(get_db),
    super_admin=Depends(require_super_admin),
):
    """
    Create a new 'admin' user bound to an organization_id.
    Only an authenticated super_admin can call this — there is no public path to it.
    """
    if body.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This endpoint only creates 'admin' accounts",
        )

    if not body.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="organization_id is required for admin accounts",
        )

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

    if not db.get(Organization, body.organization_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    user = repo.create({
        "email":           body.email,
        "hashed_password": hash_password(body.password),
        "full_name":       body.full_name,
        "role":            "admin",
        "is_active":       True,
        "student_id":      None,
        "organization_id": body.organization_id,
    })

    return UserResponse.model_validate(user)


# ── Login ─────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """
    Login with email + password.
    Works for super_admin, admin, and student. Returns JWT tokens with role embedded.
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

    if not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account uses Google Sign-In. Please sign in with Google.",
        )

    return TokenResponse(
        access_token=    create_access_token(user.id, user.role, user.student_id, user.organization_id),
        refresh_token=   create_refresh_token(user.id, user.role, user.organization_id),
        token_type=      "bearer",
        user_name=       user.full_name,
        role=            user.role,
        organization_id= user.organization_id,
        student_id=      user.student_id,
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
        "access_token": create_access_token(user.id, user.role, user.student_id, user.organization_id),
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
    admin=Depends(get_current_admin),
):
    """Admin links a user account to a student record, scoped to their own org."""
    repo = UserRepository(db)
    user = repo.get_by_id(body.user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role != "student":
        raise HTTPException(status_code=400, detail="User is not a student")

    from src.db.repositories.student_repository import StudentRepository
    student = StudentRepository(db).get_by_id_scoped(body.student_id, organization_id=admin._scoped_org_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student record not found")

    updated = repo.update(user, {"student_id": body.student_id})
    return UserResponse.model_validate(updated)


# ── List Users (Admin only) ───────────────────────────────────

@router.get("/users", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """List users visible to this admin; org-scoped for regular admins."""
    users = UserRepository(db).get_all_scoped(organization_id=admin._scoped_org_id)
    return [UserResponse.model_validate(u) for u in users]