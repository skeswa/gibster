import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.database import Base
from backend.models import SyncJob, SyncJobLog, User
from backend.sync_logger import SyncJobLogger


@pytest.fixture
def test_db():
    """Create a test database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_user(test_db):
    """Create a test user."""
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash="hashed_password",
        calendar_uuid=uuid.uuid4(),
    )
    test_db.add(user)
    test_db.commit()
    return user


@pytest.fixture
def test_sync_job(test_db, test_user):
    """Create a test sync job."""
    job = SyncJob(
        id=uuid.uuid4(),
        user_id=test_user.id,
        status="running",
        triggered_manually=True,
        started_at=datetime.now(timezone.utc),
    )
    test_db.add(job)
    test_db.commit()
    return job


class TestSyncJobLogger:
    """Test the SyncJobLogger functionality."""

    def test_log_info(self, test_db, test_sync_job):
        """Test logging info messages."""
        logger = SyncJobLogger(test_db, test_sync_job.id)

        # Log an info message
        logger.info("Test info message", test_key="test_value")

        # Verify the log was created
        logs = test_db.query(SyncJobLog).filter_by(sync_job_id=test_sync_job.id).all()
        assert len(logs) == 1

        log = logs[0]
        assert log.level == "INFO"
        assert log.message == "Test info message"
        assert log.details == {"test_key": "test_value"}
        assert log.sync_job_id == test_sync_job.id

    def test_log_error(self, test_db, test_sync_job):
        """Test logging error messages."""
        logger = SyncJobLogger(test_db, test_sync_job.id)

        # Log an error message
        logger.error("Test error message", error_code=500, error_type="ServerError")

        # Verify the log was created
        logs = test_db.query(SyncJobLog).filter_by(sync_job_id=test_sync_job.id).all()
        assert len(logs) == 1

        log = logs[0]
        assert log.level == "ERROR"
        assert log.message == "Test error message"
        assert log.details == {"error_code": 500, "error_type": "ServerError"}

    def test_log_warning(self, test_db, test_sync_job):
        """Test logging warning messages."""
        logger = SyncJobLogger(test_db, test_sync_job.id)

        # Log a warning message
        logger.warning("Test warning message", retry_count=3)

        # Verify the log was created
        logs = test_db.query(SyncJobLog).filter_by(sync_job_id=test_sync_job.id).all()
        assert len(logs) == 1

        log = logs[0]
        assert log.level == "WARNING"
        assert log.message == "Test warning message"
        assert log.details == {"retry_count": 3}

    def test_log_debug(self, test_db, test_sync_job):
        """Test logging debug messages."""
        logger = SyncJobLogger(test_db, test_sync_job.id)

        # Log a debug message
        logger.debug("Test debug message", debug_info="detailed info")

        # Verify the log was created
        logs = test_db.query(SyncJobLog).filter_by(sync_job_id=test_sync_job.id).all()
        assert len(logs) == 1

        log = logs[0]
        assert log.level == "DEBUG"
        assert log.message == "Test debug message"
        assert log.details == {"debug_info": "detailed info"}

    def test_multiple_logs(self, test_db, test_sync_job):
        """Test logging multiple messages."""
        logger = SyncJobLogger(test_db, test_sync_job.id)

        # Log multiple messages
        logger.info("First message")
        logger.warning("Second message")
        logger.error("Third message")

        # Verify all logs were created
        logs = (
            test_db.query(SyncJobLog)
            .filter_by(sync_job_id=test_sync_job.id)
            .order_by(SyncJobLog.timestamp)
            .all()
        )

        assert len(logs) == 3
        assert logs[0].message == "First message"
        assert logs[1].message == "Second message"
        assert logs[2].message == "Third message"

    def test_log_with_timing(self, test_db, test_sync_job):
        """Test logging with timing information."""
        logger = SyncJobLogger(test_db, test_sync_job.id)

        import time

        start_time = time.time()
        logger.info("Starting operation")
        time.sleep(0.1)
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000

        logger.info("Operation completed", duration_ms=duration_ms)

        # Check that timing logs were created
        logs = (
            test_db.query(SyncJobLog)
            .filter_by(sync_job_id=test_sync_job.id)
            .order_by(SyncJobLog.timestamp)
            .all()
        )

        assert len(logs) == 2
        assert "Starting operation" in logs[0].message
        assert "Operation completed" in logs[1].message
        assert "duration_ms" in logs[1].details
        assert logs[1].details["duration_ms"] >= 100  # At least 100ms

    def test_log_no_details(self, test_db, test_sync_job):
        """Test logging without details."""
        logger = SyncJobLogger(test_db, test_sync_job.id)

        logger.info("Message without details")

        logs = test_db.query(SyncJobLog).filter_by(sync_job_id=test_sync_job.id).all()
        assert len(logs) == 1
        assert logs[0].details == {}

    def test_log_complex_details(self, test_db, test_sync_job):
        """Test logging with complex details."""
        logger = SyncJobLogger(test_db, test_sync_job.id)

        complex_details = {
            "bookings": [
                {"id": "123", "name": "Test Class"},
                {"id": "456", "name": "Another Class"},
            ],
            "stats": {"total": 2, "processed": 2, "errors": 0},
            "nested": {"level1": {"level2": "value"}},
        }

        logger.info("Complex log entry", **complex_details)

        logs = test_db.query(SyncJobLog).filter_by(sync_job_id=test_sync_job.id).all()
        assert len(logs) == 1
        assert logs[0].details == complex_details


class TestSyncJobLoggingIntegration:
    """Test sync job logging in the context of the full sync process."""

    def test_pagination_filtering(self, test_db, test_sync_job):
        """Test log retrieval with pagination and filtering."""
        logger = SyncJobLogger(test_db, test_sync_job.id)

        # Create logs of different levels
        for i in range(5):
            logger.info(f"Info message {i}")
        for i in range(3):
            logger.error(f"Error message {i}")
        for i in range(2):
            logger.warning(f"Warning message {i}")

        # Test filtering by level
        error_logs = (
            test_db.query(SyncJobLog)
            .filter_by(sync_job_id=test_sync_job.id, level="ERROR")
            .all()
        )
        assert len(error_logs) == 3

        # Test pagination
        all_logs = (
            test_db.query(SyncJobLog)
            .filter_by(sync_job_id=test_sync_job.id)
            .order_by(SyncJobLog.timestamp.desc())
            .limit(5)
            .all()
        )
        assert len(all_logs) == 5
