import os
from datetime import datetime, timedelta, timezone
from typing import Optional, cast
from uuid import UUID

from celery import Celery
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from logging_config import get_logger
from models import SyncJob, User
from scraper import scrape_user_bookings
from sync_logger import SyncJobLogger

# Load environment variables from backend/.env
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)

# Configure logging
logger = get_logger("worker")

# Celery configuration - make Redis optional for local development
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

# Build Redis URL from components
if REDIS_PASSWORD:
    REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0"
else:
    REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"

# Check if we're in development mode without Redis
USE_CELERY = os.getenv("USE_CELERY", "true").lower() == "true"

logger.info(
    f"Worker configuration: USE_CELERY={USE_CELERY}, REDIS_URL={REDIS_URL.split('@')[0] if REDIS_URL else 'None'}..."
)

if USE_CELERY:
    try:
        logger.info("Initializing Celery with Redis...")
        celery_app = Celery("gibster", broker=REDIS_URL, backend=REDIS_URL)

        # Test Redis connection
        logger.debug("Testing Redis connection...")
        celery_app.control.ping(timeout=1)
        logger.info("Celery with Redis initialized successfully")

        # Configure Celery beat schedule
        from celery.schedules import crontab

        celery_app.conf.update(
            beat_schedule={
                "cleanup-sync-jobs": {
                    "task": "backend.worker.cleanup_sync_jobs_task",
                    "schedule": crontab(minute="*/15"),  # Run every 15 minutes
                },
                "scrape-all-users": {
                    "task": "backend.worker.scrape_all_users",
                    "schedule": crontab(hour="*/4"),  # Run every 4 hours
                },
            },
            timezone="UTC",
        )
    except Exception as e:
        logger.warning(f"Redis not available: {e}. Running without background tasks.")
        USE_CELERY = False
        celery_app = None
else:
    logger.info("Celery disabled via USE_CELERY=false")
    celery_app = None

# Database setup for worker
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./backend/gibster_dev.db")
logger.info(f"Worker database configuration: {DATABASE_URL.split('://')[0]}://...")

if "sqlite" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False, "timeout": 20},
        pool_pre_ping=True,
    )
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


async def sync_scrape_user_with_job_tracking(
    db, user: User, job_id: Optional[UUID] = None
):
    """Async version for when Celery is not available, with job tracking"""
    logger.info(f"Starting sync_scrape_user_with_job_tracking for user: {user.email}")
    job = None
    sync_logger = None

    try:
        # Ensure database session is working
        try:
            from sqlalchemy import text

            db.execute(text("SELECT 1"))
        except Exception as db_error:
            logger.error(f"Database connection error: {db_error}")
            raise Exception("Database connection failed")

        # Create or get existing job with proper error handling
        try:
            if job_id:
                logger.debug(f"Looking for existing job: {job_id}")
                job = db.query(SyncJob).filter(SyncJob.id == job_id).first()

            if not job:
                logger.debug("Creating new sync job")
                job = SyncJob(
                    user_id=user.id,
                    status="running",
                    progress="Starting sync...",
                    triggered_manually=True,
                )
                db.add(job)
                db.commit()
                db.refresh(job)
                logger.info(f"Created sync job {job.id} for user {user.email}")

            # Initialize sync logger immediately after job creation
            sync_logger = SyncJobLogger(db, cast(UUID, job.id))

        except Exception as job_error:
            logger.error(
                f"Failed to create/retrieve sync job: {job_error}", exc_info=True
            )
            # Try to create a failed job record for visibility
            try:
                if not job:
                    job = SyncJob(
                        user_id=user.id,
                        status="failed",
                        progress="Failed to initialize sync",
                        error_message="Failed to create sync job. Please try again.",
                        triggered_manually=True,
                        completed_at=datetime.now(timezone.utc),
                    )
                    db.add(job)
                    db.commit()
                    db.refresh(job)
            except:
                logger.error("Failed to create error job record")
                db.rollback()
            raise Exception(f"Failed to initialize sync job: {str(job_error)}")
        sync_logger.info(
            f"Sync job started for user {user.email}", user_email=user.email
        )

        # Update job status with error handling
        logger.debug(f"Updating job {job.id} status to running")
        try:
            setattr(job, "status", "running")
            setattr(job, "progress", "Connecting to Gibney...")
            setattr(job, "last_updated_at", datetime.now(timezone.utc))
            db.commit()
            sync_logger.info("Job status updated to running")
        except Exception as db_error:
            logger.error(f"Failed to update job status to running: {db_error}")
            if sync_logger:
                sync_logger.error("Failed to update job status", error=db_error)
            db.rollback()
            raise

        logger.info(f"Starting scraping for user {user.email} (job {job.id})")

        # Update progress with error handling
        try:
            setattr(job, "progress", "Logging into Gibney...")
            setattr(job, "last_updated_at", datetime.now(timezone.utc))
            db.commit()
            sync_logger.info("Starting login process")
        except Exception as db_error:
            logger.warning(f"Failed to update progress: {db_error}")
            db.rollback()

        # Perform the actual scraping
        logger.debug("Starting scraper execution")
        sync_logger.info("Initiating scraper for Gibney bookings")
        scraper_start_time = datetime.now(timezone.utc)

        # Pass sync_logger to scraper
        updated_bookings = await scrape_user_bookings(db, user, sync_logger)

        sync_logger.log_timing(
            "Scraping process", scraper_start_time, bookings_found=len(updated_bookings)
        )

        # Update progress with error handling
        try:
            setattr(job, "progress", f"Processing {len(updated_bookings)} bookings...")
            setattr(job, "bookings_synced", len(updated_bookings))
            setattr(job, "last_updated_at", datetime.now(timezone.utc))
            db.commit()
            sync_logger.info(f"Found {len(updated_bookings)} bookings to process")
        except Exception as db_error:
            logger.warning(f"Failed to update booking count: {db_error}")
            db.rollback()

        # Update user's last sync time
        logger.debug("Updating user's last sync time")
        setattr(user, "last_sync_at", datetime.now(timezone.utc))
        db.commit()
        sync_logger.info("Updated user's last sync timestamp")

        # Complete the job with error handling
        try:
            setattr(job, "status", "completed")
            setattr(
                job, "progress", f"Successfully synced {len(updated_bookings)} bookings"
            )
            setattr(job, "completed_at", datetime.now(timezone.utc))
            setattr(job, "last_updated_at", datetime.now(timezone.utc))
            db.commit()

            # Note: The sync_logger.log_sync_summary is already called in scraper
            # with the correct counts, so we don't need to call it again here
            sync_logger.info("Sync completed successfully")
        except Exception as db_error:
            logger.error(f"Failed to mark job as completed: {db_error}")
            if sync_logger:
                sync_logger.error(
                    "Failed to update job completion status", error=db_error
                )
            db.rollback()
            # Don't raise here - sync was successful even if we can't update status

        # If this was a manual sync, reschedule the next automatic sync
        if getattr(job, "triggered_manually", False) and USE_CELERY and celery_app:
            logger.debug("Rescheduling next automatic sync")
            reschedule_next_sync()

        logger.info(
            f"Successfully scraped {len(updated_bookings)} bookings for {user.email} in job {job.id}"
        )

        return {
            "job_id": job.id,
            "total_bookings": len(updated_bookings),
            "successful": True,
            "message": f"Successfully synced {len(updated_bookings)} bookings",
        }

    except Exception as e:
        logger.error(f"Failed to scrape bookings for {user.email}: {e}", exc_info=True)

        # Log error to sync job logs - create logger if needed
        if not sync_logger and job:
            try:
                sync_logger = SyncJobLogger(db, cast(UUID, job.id))
            except:
                logger.error("Failed to create sync logger for error handling")

        if sync_logger:
            sync_logger.error(f"Sync failed: {str(e)}", error=e)
        else:
            logger.warning("No sync logger available to record error details")

        # Determine error type for better user feedback
        error_message = str(e)
        # Handle cryptography errors which may have empty string representation
        if not error_message and type(e).__name__ == "InvalidToken":
            error_message = "Invalid encryption token"
        elif not error_message:
            error_message = type(e).__name__

        if "Invalid credentials" in error_message or "Login failed" in error_message:
            user_friendly_error = (
                "Invalid Gibney credentials. Please update your login information."
            )
            if sync_logger:
                sync_logger.error("Authentication failed - invalid credentials")
        elif "timeout" in error_message.lower():
            user_friendly_error = (
                "Connection timed out. Gibney website may be slow or unavailable."
            )
            if sync_logger:
                sync_logger.error("Connection timeout - Gibney site may be down")
        elif (
            "network" in error_message.lower() or "connection" in error_message.lower()
        ):
            user_friendly_error = (
                "Network error. Please check your internet connection."
            )
            if sync_logger:
                sync_logger.error("Network connectivity issue")
        elif "database" in error_message.lower():
            user_friendly_error = "Database error. Please try again later."
            if sync_logger:
                sync_logger.error("Database operation failed")
        elif (
            "browser" in error_message.lower() or "playwright" in error_message.lower()
        ):
            user_friendly_error = "Browser automation error. Please contact support."
            if sync_logger:
                sync_logger.error(
                    "Browser automation failed - possible Playwright issue"
                )
        elif (
            "invalidtoken" in error_message.lower()
            or "decrypt" in error_message.lower()
        ):
            user_friendly_error = "Failed to decrypt Gibney credentials. Please update your login information."
            if sync_logger:
                sync_logger.error(
                    "Credential decryption failed - encryption key mismatch"
                )
        else:
            user_friendly_error = f"Sync error: {error_message}"
            if sync_logger:
                sync_logger.error(f"Unexpected error: {error_message}")

        if job:
            try:
                setattr(job, "status", "failed")
                setattr(job, "error_message", user_friendly_error)
                setattr(job, "progress", f"Sync failed")
                setattr(job, "completed_at", datetime.now(timezone.utc))
                setattr(job, "last_updated_at", datetime.now(timezone.utc))
                db.commit()

                if sync_logger:
                    sync_logger.info("Job marked as failed in database")
                else:
                    logger.info(
                        f"Job {job.id} marked as failed (no sync logger available)"
                    )
            except Exception as db_error:
                logger.error(f"Failed to update job status in database: {db_error}")
                db.rollback()
                # Try one more time with a fresh transaction
                try:
                    db.begin()
                    job_update = db.query(SyncJob).filter(SyncJob.id == job.id).first()
                    if job_update:
                        job_update.status = "failed"
                        job_update.error_message = user_friendly_error
                        job_update.completed_at = datetime.now(timezone.utc)
                        db.commit()
                        logger.info("Successfully updated job status on retry")
                except:
                    logger.error("Failed to update job status even on retry")
                    db.rollback()
        else:
            logger.error("No job record available to update with error status")

        return {
            "job_id": job.id if job else None,
            "successful": False,
            "error": user_friendly_error,
            "message": user_friendly_error,
        }


def sync_scrape_all_users():
    """Synchronous version for when Celery is not available"""
    logger.info("Starting sync_scrape_all_users")
    db = SessionLocal()
    try:
        # Get all users with Gibney credentials
        users = (
            db.query(User)
            .filter(
                User.gibney_email.isnot(None),
                User.gibney_password.isnot(None),
                User.is_active.is_(True),
            )
            .all()
        )

        logger.info(f"Starting scraping for {len(users)} users")

        success_count = 0
        error_count = 0

        for user in users:
            try:
                logger.debug(f"Processing user: {user.email}")
                # For sync version, we can't use async - need to use sync scraper
                from scraper import scrape_user_bookings_sync

                try:
                    updated_bookings = scrape_user_bookings_sync(db, user)
                    result = {
                        "successful": True,
                        "total_bookings": len(updated_bookings),
                        "message": f"Successfully synced {len(updated_bookings)} bookings",
                    }
                except Exception as e:
                    result = {
                        "successful": False,
                        "error": str(e),
                        "message": f"Sync failed: {str(e)}",
                    }

                if result["successful"]:
                    success_count += 1
                    logger.debug(f"Successfully processed user: {user.email}")
                else:
                    error_count += 1
                    logger.warning(
                        f"Failed to process user: {user.email} - {result.get('error', 'Unknown error')}"
                    )
            except Exception as e:
                error_count += 1
                logger.error(f"Failed to scrape bookings for {user.email}: {e}")

        logger.info(
            f"Scraping completed: {success_count} successful, {error_count} errors"
        )

        return {
            "total_users": len(users),
            "successful": success_count,
            "errors": error_count,
        }

    except Exception as e:
        logger.error(f"Error in sync_scrape_all_users: {e}")
        raise
    finally:
        logger.debug("Closing database session")
        db.close()


if USE_CELERY and celery_app:
    logger.info("Registering Celery tasks")

    @celery_app.task
    def scrape_all_users():
        """Periodic task to scrape bookings for all users"""
        logger.info("Celery task: scrape_all_users started")
        try:
            result = sync_scrape_all_users()
            logger.info(
                f"Celery task: scrape_all_users completed successfully: {result}"
            )
            return result
        except Exception as e:
            logger.error(f"Celery task: scrape_all_users failed: {e}")
            raise

    @celery_app.task
    def cleanup_sync_jobs_task():
        """Periodic task to clean up old sync jobs"""
        logger.info("Celery task: cleanup_sync_jobs_task started")
        db = SessionLocal()
        try:
            # Check for stale jobs
            stale_count = check_and_mark_stale_jobs(db)

            # Clean up old jobs
            cleaned_count = cleanup_old_sync_jobs(db)

            result = {
                "stale_jobs_marked": stale_count,
                "old_jobs_cleaned": cleaned_count,
            }

            logger.info(f"Celery task: cleanup_sync_jobs_task completed: {result}")
            return result
        except Exception as e:
            logger.error(f"Celery task: cleanup_sync_jobs_task failed: {e}")
            raise
        finally:
            db.close()

    @celery_app.task
    def scrape_user_task(user_id: str, job_id: Optional[str] = None):
        """Task to scrape bookings for a specific user with job tracking"""
        logger.info(
            f"Celery task: scrape_user_task started for user {user_id}, job {job_id}"
        )
        db = SessionLocal()
        try:
            # Convert string user_id to UUID
            user_uuid = UUID(user_id)
            user = db.query(User).filter(User.id == user_uuid).first()
            if not user:
                error_msg = f"User {user_id} not found"
                logger.error(error_msg)
                return {"successful": False, "error": error_msg}

            logger.debug(f"Found user: {user.email}")

            # Convert job_id to UUID if provided
            job_uuid = UUID(job_id) if job_id else None

            # Run async version with asyncio
            import asyncio

            result = asyncio.run(sync_scrape_user_with_job_tracking(db, user, job_uuid))

            logger.info(
                f"Celery task: scrape_user_task completed for user {user.email}: {result}"
            )
            return result

        except Exception as e:
            logger.error(f"Error scraping user {user_id}: {e}")
            return {"successful": False, "error": str(e)}
        finally:
            logger.debug("Closing database session")
            db.close()

    def reschedule_next_sync():
        """Reschedule the next automatic sync"""
        logger.info("Rescheduling next automatic sync")
        try:
            # Schedule next sync in 4 hours
            next_run_time = datetime.now(timezone.utc) + timedelta(hours=4)

            # This is a placeholder - in a real implementation you'd use a scheduler
            # like Celery Beat or APScheduler
            logger.info(f"Rescheduled next automatic sync to run at {next_run_time}")

        except Exception as e:
            logger.error(f"Failed to reschedule next sync: {e}")

else:
    logger.info("Celery not available - background tasks will run synchronously")

    def reschedule_next_sync():
        """Placeholder when Celery is not available"""
        logger.info("Reschedule requested but Celery not available")

    # Create placeholder functions for when Celery is not available
    def scrape_all_users():
        """Non-Celery version"""
        return sync_scrape_all_users()

    def scrape_user_task_sync(user_id: str, job_id: Optional[str] = None):
        """Non-Celery version - runs sync version"""
        db = SessionLocal()
        try:
            # Convert string user_id to UUID
            user_uuid = UUID(user_id)
            user = db.query(User).filter(User.id == user_uuid).first()
            if not user:
                error_msg = f"User {user_id} not found"
                logger.error(error_msg)
                return {"successful": False, "error": error_msg}

            from .scraper import scrape_user_bookings_sync

            try:
                updated_bookings = scrape_user_bookings_sync(db, user)
                return {
                    "successful": True,
                    "total_bookings": len(updated_bookings),
                    "message": f"Successfully synced {len(updated_bookings)} bookings",
                }
            except Exception as e:
                return {
                    "successful": False,
                    "error": str(e),
                    "message": f"Sync failed: {str(e)}",
                }
        finally:
            db.close()

    # Assign the sync version to the same name for compatibility
    scrape_user_task = scrape_user_task_sync


# Rate limiting for stale job checks - store last check time
_last_stale_check_time = None
_stale_check_interval = 60  # Only check every 60 seconds


def check_and_mark_stale_jobs(db: Session, timeout_minutes: int = 10):
    """Check for stale jobs and mark them as failed"""
    global _last_stale_check_time

    # Rate limit the checks to avoid excessive database queries
    current_time = datetime.now(timezone.utc)
    if _last_stale_check_time is not None:
        time_since_last_check = (current_time - _last_stale_check_time).total_seconds()
        if time_since_last_check < _stale_check_interval:
            logger.debug(
                f"Skipping stale job check (last checked {time_since_last_check:.1f}s ago)"
            )
            return 0

    _last_stale_check_time = current_time
    logger.debug(f"Checking for stale sync jobs (timeout: {timeout_minutes} minutes)")

    try:
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=timeout_minutes)

        # Find jobs that are still running but haven't been updated recently
        stale_jobs = (
            db.query(SyncJob)
            .filter(SyncJob.status == "running", SyncJob.last_updated_at < cutoff_time)
            .all()
        )

        if stale_jobs:
            logger.warning(f"Found {len(stale_jobs)} stale sync jobs")

            for job in stale_jobs:
                logger.warning(f"Marking job {job.id} as failed due to timeout")
                setattr(job, "status", "failed")
                setattr(
                    job,
                    "error_message",
                    f"Sync timed out after {timeout_minutes} minutes",
                )
                setattr(job, "progress", "Sync failed due to timeout")
                setattr(job, "completed_at", datetime.now(timezone.utc))
                setattr(job, "last_updated_at", datetime.now(timezone.utc))

            db.commit()
            logger.info(f"Marked {len(stale_jobs)} stale jobs as failed")
        else:
            logger.debug("No stale sync jobs found")

        return len(stale_jobs)

    except Exception as e:
        logger.error(f"Error checking for stale jobs: {e}")
        db.rollback()
        return 0


def cleanup_old_sync_jobs(db: Session, days_to_keep: int = 30):
    """Remove old sync jobs to prevent database bloat"""
    logger.info(f"Cleaning up sync jobs older than {days_to_keep} days")

    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)

        # Delete old completed or failed jobs
        old_jobs = (
            db.query(SyncJob)
            .filter(
                SyncJob.status.in_(["completed", "failed"]),
                SyncJob.started_at < cutoff_date,
            )
            .all()
        )

        if old_jobs:
            job_count = len(old_jobs)
            for job in old_jobs:
                db.delete(job)

            db.commit()
            logger.info(f"Cleaned up {job_count} old sync jobs")
            return job_count
        else:
            logger.debug("No old sync jobs to clean up")
            return 0

    except Exception as e:
        logger.error(f"Error cleaning up old sync jobs: {e}")
        db.rollback()
        return 0
