# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import MagicMock

from src.main import app
from src.db.database import Base, get_db
from src.core.security import verify_kiosk_key

# ── In-memory SQLite for tests ────────────────────────────────
SQLALCHEMY_TEST_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def override_kiosk_key():
    return True


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    """Create all tables before tests, drop after."""
    # Import all models so Base knows about them
    from src.models import Admin, Organization, Student, Attendance
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def client():
    """FastAPI test client with mocked DB and AI pipeline."""
    # Mock the AI pipeline so tests don't need GPU/models
    mock_pipeline = MagicMock()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[verify_kiosk_key] = override_kiosk_key

    # Inject mock pipeline into app.state
    app.state.pipeline = mock_pipeline

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def auth_headers(client):
    """
    Create a test admin, login, and return auth headers.
    Used by all tests that need authentication.
    """
    from src.core.security import hash_password
    from src.db.repositories.admin_repository import AdminRepository

    db = TestingSessionLocal()
    repo = AdminRepository(db)

    # Create test admin if not exists
    existing = repo.get_by_email("test@admin.com")
    if not existing:
        repo.create({
            "email": "test@admin.com",
            "hashed_password": hash_password("testpass123"),
            "full_name": "Test Admin",
            "is_active": True,
        })
    db.close()

    # Login
    response = client.post("/api/v1/auth/login", json={
        "email": "test@admin.com",
        "password": "testpass123",
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def test_org(client, auth_headers):
    """Create a test organization."""
    db = TestingSessionLocal()
    from src.db.repositories.base import BaseRepository
    from src.models.organization import Organization

    repo = BaseRepository(db, Organization)
    org = repo.create({"name": "Test Faculty", "description": "Test org"})
    db.close()
    return org
