# src/schemas/user.py
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Literal


# ── Request Schemas ───────────────────────────────────────────

class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: Literal["super_admin", "admin", "student"] = "student"
    # Public /auth/signup only ever accepts "student" (enforced in Step 3).
    # "admin" / "super_admin" are only reachable via the protected
    # admin-creation endpoint, which reuses this same request shape.
    organization_id: int | None = None
    # Required when role = "admin"; ignored otherwise.
    student_code: str | None = None
    # Required when role = "student"; verified against students table
    # to auto-bind student_id (Step 3).


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
    role: Literal["super_admin", "admin", "student"]
    organization_id: int | None
    student_id: int | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user_name: str
    role: Literal["super_admin", "admin", "student"]
    organization_id: int | None = None
    student_id: int | None = None