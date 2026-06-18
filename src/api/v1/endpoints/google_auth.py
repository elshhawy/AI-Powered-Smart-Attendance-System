# src/api/v1/endpoints/google_auth.py
import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel

from src.db.database import get_db
from src.db.repositories.user_repository import UserRepository
from src.core.security import create_access_token, create_refresh_token
from src.schemas.user import TokenResponse

router = APIRouter(prefix="/auth", tags=["Google OAuth"])

GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


class GoogleTokenRequest(BaseModel):
    access_token: str


@router.post("/google/token", response_model=TokenResponse)
async def google_token_login(
    body: GoogleTokenRequest,
    db: Session = Depends(get_db),
):
    """
    Frontend sends Google access token → we verify with Google → return JWT.
    """
    async with httpx.AsyncClient() as client:
        info_res = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {body.access_token}"},
        )

    if info_res.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    google_user = info_res.json()
    google_id   = google_user.get("sub")
    email       = google_user.get("email")
    full_name   = google_user.get("name", email)

    if not google_id or not email:
        raise HTTPException(status_code=400, detail="Missing data from Google")

    repo = UserRepository(db)
    user = repo.get_by_google_id(google_id)

    if not user:
        user = repo.get_by_email(email)
        if user:
            user = repo.update(user, {"google_id": google_id})
        else:
            raise HTTPException(
                status_code=403,
                detail="No account found for this Google email. Ask your super_admin to create one first.",
            )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account is deactivated")

    return TokenResponse(
        access_token=  create_access_token(user.id, user.role, user.student_id),
        refresh_token= create_refresh_token(user.id, user.role),
        token_type=    "bearer",
        user_name=     user.full_name,
        role=          user.role,
        student_id=    user.student_id,
    )