# src/schemas/auth.py
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """
    What the admin sends to POST /auth/login.
    EmailStr automatically validates that the email is a valid format.
    """
    email:    EmailStr
    password: str


class TokenResponse(BaseModel):
    """
    What the login endpoint returns.
    The admin stores both tokens. Access token goes in every request header.
    Refresh token is saved and used only when the access token expires.
    """
    access_token:  str
    refresh_token: str
    token_type:    str    # Always "bearer"
    admin_name:    str    # Shown in the UI: "Welcome, Ahmed"


class RefreshRequest(BaseModel):
    refresh_token: str


class AdminCreate(BaseModel):
    """Used by the CLI script to create a new admin."""
    email:     EmailStr
    password:  str
    full_name: str


class AdminResponse(BaseModel):
    """Returned by GET /auth/me."""
    id:        int
    email:     str
    full_name: str
    is_active: bool

    # This line is REQUIRED.
    # Without it, Pydantic cannot read attributes from a SQLAlchemy object.
    # SQLAlchemy uses lazy-loading — Pydantic needs to know to treat it
    # like a dict rather than a plain Python object.
    model_config = {"from_attributes": True}