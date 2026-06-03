# src/schemas/course.py
from datetime import time
from pydantic import BaseModel, Field


# ── Course Schemas ────────────────────────────────────────────

class CourseCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, example="Artificial Intelligence")
    code: str = Field(..., min_length=1, max_length=50, example="CS401")
    description: str | None = Field(None, example="Introduction to AI concepts")
    organization_id: int = Field(..., gt=0, example=1)


class CourseUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=255)
    code: str | None = Field(None, min_length=1, max_length=50)
    description: str | None = None
    is_active: bool | None = None


class CourseResponse(BaseModel):
    id: int
    organization_id: int
    name: str
    code: str
    description: str | None
    is_active: bool
    sessions: list["CourseSessionResponse"] = []

    model_config = {"from_attributes": True}


class CourseListResponse(BaseModel):
    courses: list[CourseResponse]
    total: int


# ── CourseSession Schemas ─────────────────────────────────────

class CourseSessionCreate(BaseModel):
    session_type: str = Field(
        ...,
        min_length=1,
        max_length=50,
        example="lecture",
        description="lecture | section | lab | tutorial | exam | or any custom type",
    )
    day_of_week: int = Field(
        ...,
        ge=0,
        le=6,
        example=6,
        description="0=Monday, 1=Tuesday, ..., 6=Sunday",
    )
    start_time: time = Field(..., example="10:00:00")
    end_time: time = Field(..., example="11:00:00")
    late_after_minutes: int = Field(
        default=15,
        ge=0,
        le=120,
        example=15,
        description="Minutes after start_time before student is considered late",
    )


class CourseSessionUpdate(BaseModel):
    session_type: str | None = None
    day_of_week: int | None = Field(None, ge=0, le=6)
    start_time: time | None = None
    end_time: time | None = None
    late_after_minutes: int | None = Field(None, ge=0, le=120)
    is_active: bool | None = None


class CourseSessionResponse(BaseModel):
    id: int
    course_id: int
    session_type: str
    day_of_week: int
    start_time: time
    end_time: time
    late_after_minutes: int
    is_active: bool

    model_config = {"from_attributes": True}


# Active session info returned with attendance
class ActiveSessionInfo(BaseModel):
    session_id: int
    course_name: str
    course_code: str
    session_type: str
    start_time: time
    end_time: time

    model_config = {"from_attributes": True}


# Update forward ref
CourseResponse.model_rebuild()