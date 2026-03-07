# src/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Attendance System API",
    description="Admin-only attendance management with face recognition",
    version="1.0.0",
)

# CORS — allows the Streamlit frontend (running on port 8501)
# to make requests to the API (running on port 8000).
# Without this, browsers block cross-origin requests.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],  # Streamlit's port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and register routers
from src.api.v1.endpoints.auth import router as auth_router
app.include_router(auth_router, prefix="/api/v1")

@app.get("/")
def root():
    return {"status": "running", "docs": "/docs"}