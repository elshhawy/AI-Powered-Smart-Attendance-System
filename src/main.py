# src/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.v1.endpoints.auth import router as auth_router
from src.api.v1.endpoints.students import router as students_router
from src.api.v1.endpoints.attendance import router as attendance_router

app = FastAPI(
    title="Attendance System API",
    description="Admin-only attendance management with face recognition",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router,       prefix="/api/v1")
app.include_router(students_router,   prefix="/api/v1")
app.include_router(attendance_router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "AI-Powered Smart Attendance System", "docs": "/docs"}