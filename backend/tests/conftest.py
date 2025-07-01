import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base, get_db
from backend.main import app
from backend.models import User


@pytest.fixture(scope="function")
def test_db():
    """Create a temporary SQLite database for testing"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
        db_path = tmp_file.name

    # Create test database
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    yield TestingSessionLocal()

    # Cleanup
    app.dependency_overrides.clear()
    os.unlink(db_path)


@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client for the FastAPI app"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {"email": "test@example.com", "password": "testpassword123"}


@pytest.fixture
def sample_credentials():
    """Sample Gibney credentials for testing"""
    return {"gibney_email": "gibney@example.com", "gibney_password": "gibneypass123"}


@pytest.fixture
def sample_booking_data():
    """Sample booking data for testing"""
    return [
        {
            "id": "a27Pb000000001",
            "name": "R-490015",
            "start_time": "2024-01-15T10:00:00Z",
            "end_time": "2024-01-15T12:00:00Z",
            "studio": "Studio A",
            "location": "280 Broadway",
            "status": "Confirmed",
            "price": 50.00,
            "record_url": "https://gibney.my.site.com/s/rental-form?Id=a27Pb000000001",
        },
        {
            "id": "a27Pb000000002",
            "name": "R-490016",
            "start_time": "2024-01-16T14:00:00Z",
            "end_time": "2024-01-16T16:00:00Z",
            "studio": "Studio B",
            "location": "890 Broadway",
            "status": "Confirmed",
            "price": 75.00,
            "record_url": "https://gibney.my.site.com/s/rental-form?Id=a27Pb000000002",
        },
    ]
