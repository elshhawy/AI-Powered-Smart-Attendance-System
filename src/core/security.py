# src/core/security.py
import bcrypt
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from src.core.config import settings
from src.db.database import get_db

ALGORITHM             = "HS256"
ACCESS_EXPIRE_MINUTES = 30
REFRESH_EXPIRE_DAYS   = 7

http_bearer = HTTPBearer(auto_error=False)


# ── Password ──────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# ── Tokens ────────────────────────────────────────────────────

def create_access_token(user_id: int, role: str, student_id: int | None = None) -> str:
    """
    Create JWT access token with role and student_id embedded.
    This is what allows the frontend to know the user's role immediately.
    """
    payload = {
        "sub":        str(user_id),
        "role":       role,
        "student_id": student_id,
        "exp":        datetime.utcnow() + timedelta(minutes=ACCESS_EXPIRE_MINUTES),
        "type":       "access",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: int, role: str) -> str:
    payload = {
        "sub":  str(user_id),
        "role": role,
        "exp":  datetime.utcnow() + timedelta(days=REFRESH_EXPIRE_DAYS),
        "type": "refresh",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str, expected_type: str) -> dict:
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    if payload.get("type") != expected_type:
        raise JWTError(f"Wrong token type: expected '{expected_type}'")
    return payload


# ── Dependencies ──────────────────────────────────────────────

def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(http_bearer),
    db: Session = Depends(get_db),
):
    """
    Base dependency — works for ANY logged-in user (admin or student).
    Returns the User object from the users table.
    """
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise exc

    try:
        payload = verify_token(credentials.credentials, "access")
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise exc

    from src.db.repositories.user_repository import UserRepository
    user = UserRepository(db).get_by_id(user_id)

    if user is None:
        raise exc
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account is deactivated")

    return user


def require_admin(user=Depends(get_current_user)):
    """
    Dependency for admin-only endpoints.
    Raises 403 if the user is not an admin.
    """
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


def require_student(user=Depends(get_current_user)):
    """
    Dependency for student-only endpoints.
    Raises 403 if the user is not a student.
    """
    if user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access required",
        )
    return user


# ── Backward compatibility ────────────────────────────────────
# Keep get_current_admin working for existing endpoints
# so we don't have to change all endpoints at once

def get_current_admin(user=Depends(require_admin)):
    """
    Backward-compatible alias for require_admin.
    Existing endpoints using Depends(get_current_admin) still work.
    """
    return user


# ── Kiosk key ─────────────────────────────────────────────────

def verify_kiosk_key(x_api_key: str | None = Header(default=None)):
    if not x_api_key or x_api_key != settings.KIOSK_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing kiosk API key",
        )
    return True