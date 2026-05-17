# src/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.v1.endpoints.auth import router as auth_router
from src.api.v1.endpoints.students import router as students_router
from src.api.v1.endpoints.attendance import router as attendance_router
from src.api.v1.endpoints.chat import router as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    from src.ai.recognition_pipeline import RecognitionPipeline
    print("Loading AI models — this takes ~30 seconds on first run...")
    app.state.pipeline = RecognitionPipeline()
    print("AI models loaded. Ready to accept requests.")
    yield


app = FastAPI(
    title="AI-Powered Smart Attendance System",
    description="Face recognition based attendance system",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://attendance_ui:3000",
        "http://localhost:8501",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router,       prefix="/api/v1")
app.include_router(students_router,   prefix="/api/v1")
app.include_router(attendance_router, prefix="/api/v1")
app.include_router(chat_router,       prefix="/api/v1")


@app.get("/")
def root():
    return {"message": "AI-Powered Smart Attendance System", "docs": "/docs"}
