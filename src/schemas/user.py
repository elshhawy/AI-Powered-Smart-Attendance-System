# src/schemas/user.py
from pydantic import BaseModel, EmailStr
from datetime import datetime


# ── Request Schemas ───────────────────────────────────────────

class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "admin"
    # role = "admin" | "student"
    # student must also provide student_id to link their account


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LinkStudentRequest(BaseModel):
    """Admin uses this to link a student record to a user account."""
    user_id: int
    student_id: int


# ── Response Schemas ──────────────────────────────────────────

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    student_id: int | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user_name: str
    role: str
    student_id: int | None = None