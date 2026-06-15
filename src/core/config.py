# src/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # Auth
    SECRET_KEY: str
    KIOSK_API_KEY: str

    # Google OAuth
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"

    # External services
    GROQ_API_KEY: str
    EMAIL_FROM: str
    EMAIL_APP_PASSWORD: str
    ADMIN_ALERT_EMAIL: str

    # FAISS
    FAISS_INDEX_PATH: str
    FAISS_ID_MAP_PATH: str
    SIMILARITY_THRESHOLD: float = 0.8

    # Session timing (fallback if no active course session)
    SESSION_START_HOUR: int = 9
    SESSION_START_MINUTE: int = 0
    LATE_THRESHOLD_MINUTES: int = 15

    class Config:
        env_file = ".env"
        extra = "ignore"  # allow VITE_* and other frontend-only vars in .env

settings = Settings()