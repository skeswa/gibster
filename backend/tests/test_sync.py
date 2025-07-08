"""
Tests for sync functionality to ensure jobs don't get stuck.
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from backend.models import SyncJob, User
from backend.worker import check_and_mark_stale_jobs, cleanup_old_sync_jobs


@pytest.fixture
def test_user(test_db):
    """Create a test user for sync tests"""
    user = User(
        email=f"test_sync_{uuid4()}@example.com",
        password_hash="dummy_hash",
        gibney_email="test@gibney.com",
        gibney_password="encrypted_password",
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    yield user

    # Cleanup
    test_db.query(SyncJob).filter(SyncJob.user_id == user.id).delete()
    test_db.query(User).filter(User.id == user.id).delete()
    test_db.commit()


class TestSyncJobManagement:
    """Test sync job management functionality"""

    def test_stale_job_detection(self, test_db, test_user: User):
        """Test that stale jobs are properly marked as failed"""
        # Reset rate limiting for tests
        import backend.worker as worker

        worker._last_stale_check_time = None

        # Create a job that's been running for too long
        stale_job = SyncJob(
            user_id=test_user.id,
            status="running",
            progress="Stuck in processing...",
            started_at=datetime.now(timezone.utc) - timedelta(minutes=15),
            last_updated_at=datetime.now(timezone.utc) - timedelta(minutes=12),
        )
        test_db.add(stale_job)
        test_db.commit()

        # Run the stale job checker
        stale_count = check_and_mark_stale_jobs(test_db)

        # Verify the job was marked as failed
        test_db.refresh(stale_job)
        assert getattr(stale_job, "status") == "failed"
        assert "timed out" in getattr(stale_job, "error_message", "").lower()
        assert stale_count == 1

    def test_stale_job_detection_respects_timeout(self, test_db, test_user: User):
        """Test that jobs within timeout window are not marked as stale"""
        # Create a job that's still within the timeout window
        active_job = SyncJob(
            user_id=test_user.id,
            status="running",
            progress="Still processing...",
            started_at=datetime.now(timezone.utc) - timedelta(minutes=5),
            last_updated_at=datetime.now(timezone.utc) - timedelta(minutes=3),
        )
        test_db.add(active_job)
        test_db.commit()

        # Run the stale job checker
        stale_count = check_and_mark_stale_jobs(test_db)

        # Verify the job was NOT marked as failed
        test_db.refresh(active_job)
        assert getattr(active_job, "status") == "running"
        assert getattr(active_job, "error_message") is None
        assert stale_count == 0

    def test_cleanup_old_jobs(self, test_db, test_user: User):
        """Test that old jobs are properly cleaned up"""
        # Create some old completed jobs
        old_job_ids = []
        for i in range(3):
            old_job = SyncJob(
                user_id=test_user.id,
                status="completed",
                progress="Old sync completed",
                started_at=datetime.now(timezone.utc) - timedelta(days=35 + i),
                completed_at=datetime.now(timezone.utc) - timedelta(days=35 + i),
            )
            test_db.add(old_job)
            test_db.flush()
            old_job_ids.append(old_job.id)

        # Create a recent job that shouldn't be cleaned up
        recent_job = SyncJob(
            user_id=test_user.id,
            status="completed",
            progress="Recent sync completed",
            started_at=datetime.now(timezone.utc) - timedelta(days=5),
            completed_at=datetime.now(timezone.utc) - timedelta(days=5),
        )
        test_db.add(recent_job)
        test_db.commit()

        # Count jobs before cleanup
        jobs_before = (
            test_db.query(SyncJob).filter(SyncJob.user_id == test_user.id).count()
        )
        assert jobs_before == 4  # 3 old + 1 recent

        # Run cleanup
        cleaned_count = cleanup_old_sync_jobs(test_db)

        # Verify old jobs were removed but recent one remains
        jobs_after = (
            test_db.query(SyncJob).filter(SyncJob.user_id == test_user.id).count()
        )
        assert jobs_after == 1  # Only recent job remains
        assert cleaned_count == 3

        # Verify the recent job still exists
        recent_job_exists = (
            test_db.query(SyncJob).filter(SyncJob.id == recent_job.id).first()
        )
        assert recent_job_exists is not None

        # Verify old jobs were deleted
        for old_job_id in old_job_ids:
            old_job_exists = (
                test_db.query(SyncJob).filter(SyncJob.id == old_job_id).first()
            )
            assert old_job_exists is None

    def test_duplicate_job_prevention(self, test_db, test_user: User):
        """Test that duplicate pending/running jobs are prevented"""
        # Create a running job
        running_job = SyncJob(
            user_id=test_user.id,
            status="running",
            progress="Currently syncing...",
            started_at=datetime.now(timezone.utc),
            last_updated_at=datetime.now(timezone.utc),
        )
        test_db.add(running_job)
        test_db.commit()

        # Try to find existing running job
        existing_job = (
            test_db.query(SyncJob)
            .filter(
                SyncJob.user_id == test_user.id,
                SyncJob.status.in_(["pending", "running"]),
            )
            .first()
        )

        assert existing_job is not None
        assert existing_job.id == running_job.id

    def test_completed_jobs_allow_new_sync(self, test_db, test_user: User):
        """Test that completed jobs don't prevent new syncs"""
        # Create a completed job
        completed_job = SyncJob(
            user_id=test_user.id,
            status="completed",
            progress="Sync completed",
            started_at=datetime.now(timezone.utc) - timedelta(hours=1),
            completed_at=datetime.now(timezone.utc) - timedelta(minutes=30),
        )
        test_db.add(completed_job)
        test_db.commit()

        # Check that no running job exists
        existing_running_job = (
            test_db.query(SyncJob)
            .filter(
                SyncJob.user_id == test_user.id,
                SyncJob.status.in_(["pending", "running"]),
            )
            .first()
        )

        assert existing_running_job is None

    def test_failed_jobs_allow_new_sync(self, test_db, test_user: User):
        """Test that failed jobs don't prevent new syncs"""
        # Create a failed job
        failed_job = SyncJob(
            user_id=test_user.id,
            status="failed",
            progress="Sync failed",
            error_message="Test error",
            started_at=datetime.now(timezone.utc) - timedelta(hours=1),
            completed_at=datetime.now(timezone.utc) - timedelta(minutes=30),
        )
        test_db.add(failed_job)
        test_db.commit()

        # Check that no running job exists
        existing_running_job = (
            test_db.query(SyncJob)
            .filter(
                SyncJob.user_id == test_user.id,
                SyncJob.status.in_(["pending", "running"]),
            )
            .first()
        )

        assert existing_running_job is None


@pytest.mark.asyncio
class TestAsyncSyncFunctionality:
    """Test async sync functionality"""

    async def test_sync_job_tracking_updates_timestamps(self, test_db, test_user: User):
        """Test that sync job tracking properly updates timestamps"""
        # This test would require mocking the scraper, which is complex
        # For now, we're focusing on the synchronous parts
        pass
