import os
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from celery import Celery
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .logging_config import get_logger
from .models import SyncJob, User
from .scraper import scrape_user_bookings

load_dotenv()

# Configure logging
logger = get_logger("worker")

# Celery configuration - make Redis optional for local development
# Support both REDIS_URL format and separate REDIS_HOST/PASSWORD
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

# Build Redis URL from components if not directly provided
if os.getenv("REDIS_URL"):
    REDIS_URL = os.getenv("REDIS_URL")
else:
    if REDIS_PASSWORD:
        REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0"
    else:
        REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"

# Check if we're in development mode without Redis
USE_CELERY = os.getenv("USE_CELERY", "true").lower() == "true"

logger.info(
    f"Worker configuration: USE_CELERY={USE_CELERY}, REDIS_URL={REDIS_URL.split('@')[0]}..."
)

if USE_CELERY:
    try:
        logger.info("Initializing Celery with Redis...")
        celery_app = Celery("gibster", broker=REDIS_URL, backend=REDIS_URL)

        # Test Redis connection
        logger.debug("Testing Redis connection...")
        celery_app.control.ping(timeout=1)
        logger.info("Celery with Redis initialized successfully")
    except Exception as e:
        logger.warning(f"Redis not available: {e}. Running without background tasks.")
        USE_CELERY = False
        celery_app = None
else:
    logger.info("Celery disabled via USE_CELERY=false")
    celery_app = None

# Database setup for worker
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./gibster_dev.db")
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

    try:
        # Create or get existing job
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

        # Update job status
        logger.debug(f"Updating job {job.id} status to running")
        setattr(job, "status", "running")
        setattr(job, "progress", "Connecting to Gibney...")
        db.commit()

        logger.info(f"Starting scraping for user {user.email} (job {job.id})")

        # Update progress
        setattr(job, "progress", "Logging into Gibney...")
        db.commit()

        # Perform the actual scraping
        logger.debug("Starting scraper execution")
        updated_bookings = await scrape_user_bookings(db, user)

        # Update progress
        setattr(job, "progress", f"Processing {len(updated_bookings)} bookings...")
        setattr(job, "bookings_synced", len(updated_bookings))
        db.commit()

        # Update user's last sync time
        logger.debug("Updating user's last sync time")
        setattr(user, "last_sync_at", datetime.utcnow())
        db.commit()

        # Complete the job
        setattr(job, "status", "completed")
        setattr(
            job, "progress", f"Successfully synced {len(updated_bookings)} bookings"
        )
        setattr(job, "completed_at", datetime.utcnow())
        db.commit()

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
        logger.error(f"Failed to scrape bookings for {user.email}: {e}")

        if job:
            setattr(job, "status", "failed")
            setattr(job, "error_message", str(e))
            setattr(job, "progress", f"Sync failed: {str(e)}")
            setattr(job, "completed_at", datetime.utcnow())
            db.commit()

        return {
            "job_id": job.id if job else None,
            "successful": False,
            "error": str(e),
            "message": f"Sync failed: {str(e)}",
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
                from .scraper import scrape_user_bookings_sync

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
    def scrape_user_task(user_id: str, job_id: Optional[str] = None):
        """Task to scrape bookings for a specific user with job tracking"""
        logger.info(
            f"Celery task: scrape_user_task started for user {user_id}, job {job_id}"
        )
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                error_msg = f"User {user_id} not found"
                logger.error(error_msg)
                return {"successful": False, "error": error_msg}

            logger.debug(f"Found user: {user.email}")

            # Convert job_id to UUID if provided
            job_uuid = UUID(job_id) if job_id else None

            result = sync_scrape_user_with_job_tracking(db, user, job_uuid)
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
            next_run_time = datetime.utcnow() + timedelta(hours=4)

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
            user = db.query(User).filter(User.id == user_id).first()
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
