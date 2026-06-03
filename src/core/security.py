# src/core/security.py
import bcrypt
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from src.core.config import settings
from src.db.database import get_db

# ── Constants ─────────────────────────────────────────────────────────────────
ALGORITHM              = "HS256"
ACCESS_EXPIRE_MINUTES  = 30
REFRESH_EXPIRE_DAYS    = 7

# oauth2_scheme tells FastAPI:
# "look for a Bearer token in the Authorization header"
http_bearer = HTTPBearer(auto_error=False)


# ── Password hashing ──────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    """
    Hash a plain-text password using bcrypt.
    bcrypt automatically generates a random salt each time,
    so the same password produces a different hash on every call.
    This is intentional — it prevents rainbow table attacks.
    """
    return bcrypt.hashpw(
        plain.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """
    Check if a plain-text password matches a stored bcrypt hash.
    Returns True if they match, False if not.
    """
    return bcrypt.checkpw(
        plain.encode("utf-8"),
        hashed.encode("utf-8")
    )


# ── Token creation ────────────────────────────────────────────────────────────

def create_access_token(admin_id: int) -> str:
    """
    Create a JWT access token for an admin.
    The token contains:
      - sub: the admin's database id (as a string)
      - exp: expiry timestamp (30 minutes from now)
      - type: "access" (so we can reject refresh tokens used as access tokens)
    """
    payload = {
        "sub":  str(admin_id),
        "exp":  datetime.utcnow() + timedelta(minutes=ACCESS_EXPIRE_MINUTES),
        "type": "access",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(admin_id: int) -> str:
    """
    Create a JWT refresh token.
    Longer lifetime (7 days) but only accepted at /auth/refresh.
    """
    payload = {
        "sub":  str(admin_id),
        "exp":  datetime.utcnow() + timedelta(days=REFRESH_EXPIRE_DAYS),
        "type": "refresh",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str, expected_type: str) -> dict:
    """
    Decode and validate a JWT token.
    Raises JWTError if signature invalid, expired, or wrong type.
    """
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])

    if payload.get("type") != expected_type:
        raise JWTError(
            f"Wrong token type: expected '{expected_type}', "
            f"got '{payload.get('type')}'"
        )
    return payload


# ── FastAPI dependencies ──────────────────────────────────────────────────────

def get_current_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(http_bearer),
    db: Session = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise credentials_exception

    token = credentials.credentials

    try:
        payload  = verify_token(token, "access")
        admin_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise credentials_exception

    from src.db.repositories.admin_repository import AdminRepository
    admin = AdminRepository(db).get_by_id(admin_id)

    if admin is None:
        raise credentials_exception
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin account is deactivated",
        )
    return admin


def verify_kiosk_key(x_api_key: str | None = Header(default=None)):
    """
    FastAPI dependency for the camera/kiosk attendance endpoint.
    Authenticates using a static API key stored in .env.
    """
    if not x_api_key or x_api_key != settings.KIOSK_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing kiosk API key",
        )
    return Trueي