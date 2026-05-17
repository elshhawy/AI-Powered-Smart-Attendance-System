# src/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.db.repositories.admin_repository import AdminRepository
from src.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    get_current_admin,
)
from src.schemas.auth import LoginRequest, TokenResponse, RefreshRequest, AdminResponse
from src.models.admin import Admin
from jose import JWTError

router = APIRouter(prefix="/auth", tags=["Authentication"])



@router.post("/login", response_model=TokenResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """
    Admin login. Returns access + refresh tokens on success.

    SECURITY RULE — give the SAME error for wrong email AND wrong password:
        "Incorrect email or password"

    Never say "email not found" or "wrong password" separately.
    Differentiating them tells attackers which emails exist in the system.
    An attacker could enumerate all admin emails by trying random ones
    and watching which error they get.

    We also call verify_password() EVEN IF the admin is not found.
    This is called a "dummy verification" — it prevents timing attacks
    where an attacker measures response time to detect missing accounts.
    """
    repo  = AdminRepository(db)
    admin = repo.get_by_email(credentials.email)

    # Dummy hash — used when admin not found to prevent timing attacks
    dummy_hash = "$2b$12$KIXbMHjwrVkKQzX9X9X9XeWQKIXbMHjwrVkKQzX9X9X9Xe"

    password_to_check = admin.hashed_password if admin else dummy_hash

    if not admin or not verify_password(credentials.password, password_to_check):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account has been deactivated",
        )

    return {
        "access_token":  create_access_token(admin.id),
        "refresh_token": create_refresh_token(admin.id),
        "token_type":    "bearer",
        "admin_name":    admin.full_name,
    }
    
    
    
@router.post("/refresh")
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    """
    Exchange a refresh token for a new access token.
    Called automatically by the frontend when the access token expires.
    """
    try:
        payload  = verify_token(body.refresh_token, "refresh")
        admin_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    admin = AdminRepository(db).get_by_id(admin_id)
    if not admin or not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin not found or deactivated",
        )

    return {
        "access_token": create_access_token(admin.id),
        "token_type":   "bearer",
    }


@router.get("/me", response_model=AdminResponse)
def get_me(admin: Admin = Depends(get_current_admin)):
    """
    Returns the current admin's info.
    Used by the Streamlit frontend to show "Welcome, [name]" in the sidebar.
    No db parameter needed — get_current_admin already loaded the admin.
    """
    return admin
  
  



