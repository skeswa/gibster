import uuid
from datetime import datetime
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
        started_at=datetime.utcnow(),
    )
    test_db.add(job)
    test_db.commit()
    return job


class TestSyncJobLoggerSimple:
    """Simple test to verify sync job logging works."""

    def test_complete_sync_flow_logging(self, test_db, test_user):
        """Test a complete sync flow with logging."""
        # Create a sync job
        job = SyncJob(
            id=uuid.uuid4(),
            user_id=test_user.id,
            status="running",
            triggered_manually=True,
            started_at=datetime.utcnow(),
        )
        test_db.add(job)
        test_db.commit()

        # Create logger
        logger = SyncJobLogger(test_db, job.id)

        # Simulate sync flow with logging
        logger.info("Sync job started", user_id=str(test_user.id))
        logger.info("Connecting to Gibney...")
        logger.info("Logging in...", username="test@gibney.com")
        logger.info("Login successful")
        logger.info("Fetching bookings...")
        logger.info("Found 5 bookings", count=5)
        logger.info("Processing bookings...")
        logger.warning("Skipped 1 cancelled booking", booking_id="123")
        logger.info("Sync completed successfully", total_bookings=4)

        # Update job status
        job.status = "completed"
        job.bookings_synced = 4
        job.completed_at = datetime.utcnow()
        test_db.commit()

        # Verify logs
        logs = (
            test_db.query(SyncJobLog)
            .filter_by(sync_job_id=job.id)
            .order_by(SyncJobLog.timestamp)
            .all()
        )

        assert len(logs) == 9

        # Check log levels
        info_logs = [log for log in logs if log.level == "INFO"]
        warning_logs = [log for log in logs if log.level == "WARNING"]

        assert len(info_logs) == 8
        assert len(warning_logs) == 1

        # Check specific messages
        log_messages = [log.message for log in logs]
        assert "Sync job started" in log_messages[0]
        assert "Sync completed successfully" in log_messages[-1]
        assert any("Skipped 1 cancelled booking" in msg for msg in log_messages)

        # Check details
        start_log = logs[0]
        assert start_log.details.get("user_id") == str(test_user.id)

        completion_log = logs[-1]
        assert completion_log.details.get("total_bookings") == 4

    def test_failed_sync_logging(self, test_db, test_user):
        """Test logging for a failed sync."""
        # Create a sync job
        job = SyncJob(
            id=uuid.uuid4(),
            user_id=test_user.id,
            status="running",
            triggered_manually=True,
            started_at=datetime.utcnow(),
        )
        test_db.add(job)
        test_db.commit()

        # Create logger
        logger = SyncJobLogger(test_db, job.id)

        # Simulate failed sync flow
        logger.info("Sync job started", user_id=str(test_user.id))
        logger.info("Connecting to Gibney...")
        logger.error("Login failed - invalid credentials")
        logger.error("Sync failed", error="Authentication error")

        # Update job status
        job.status = "failed"
        job.error_message = "Invalid credentials"
        job.completed_at = datetime.utcnow()
        test_db.commit()

        # Verify logs
        logs = (
            test_db.query(SyncJobLog)
            .filter_by(sync_job_id=job.id)
            .order_by(SyncJobLog.timestamp)
            .all()
        )

        assert len(logs) == 4

        # Check error logs
        error_logs = [log for log in logs if log.level == "ERROR"]
        assert len(error_logs) == 2

        # Check messages
        assert any("Login failed" in log.message for log in error_logs)
        assert any("Sync failed" in log.message for log in error_logs)
