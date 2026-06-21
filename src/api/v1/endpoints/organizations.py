# src/api/v1/endpoints/organizations.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.db.database import get_db
from src.core.security import require_super_admin
from src.models.organization import Organization

router = APIRouter(prefix="/organizations", tags=["Organizations"])

class OrganizationCreate(BaseModel):
    name: str
    description: str | None = None

class OrganizationResponse(OrganizationCreate):
    id: int
    model_config = {"from_attributes": True}

@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
def create_organization(
    body: OrganizationCreate,
    db: Session = Depends(get_db),
    admin=Depends(require_super_admin),
):
    """Super Admin only: Create a new organization faculty/department."""
    org = Organization(name=body.name, description=body.description)
    db.add(org)
    db.commit()
    db.refresh(org)
    return org
  
@router.get("", response_model=list[OrganizationResponse])
def list_organizations(
    db: Session = Depends(get_db),
    admin=Depends(require_super_admin),
):
    """Super Admin only: Get all organizations."""
    return db.query(Organization).all()