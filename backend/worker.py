import logging
import os
from datetime import timedelta

from celery import Celery
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import User
from .scraper import scrape_user_bookings

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Celery configuration - make Redis optional for local development
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Check if we're in development mode without Redis
USE_CELERY = os.getenv("USE_CELERY", "true").lower() == "true"

if USE_CELERY:
    try:
        celery_app = Celery("gibster", broker=REDIS_URL, backend=REDIS_URL)
        # Test Redis connection
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
if "sqlite" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False, "timeout": 20},
        pool_pre_ping=True,
    )
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def sync_scrape_all_users():
    """Synchronous version for when Celery is not available"""
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
                scrape_user_bookings(db, user)
                success_count += 1
                logger.info(f"Successfully scraped bookings for {user.email}")
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
        db.close()


if USE_CELERY and celery_app:

    @celery_app.task
    def scrape_all_users():
        """Periodic task to scrape bookings for all users"""
        return sync_scrape_all_users()

    @celery_app.task
    def scrape_user_task(user_id: str):
        """Task to scrape bookings for a specific user"""
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User with ID {user_id} not found")

            scrape_user_bookings(db, user)
            logger.info(f"Successfully scraped bookings for user {user.email}")

            return {"message": f"Scraped bookings for {user.email}"}

        except Exception as e:
            logger.error(f"Error scraping user {user_id}: {e}")
            raise
        finally:
            db.close()

    # Configure periodic tasks
    celery_app.conf.beat_schedule = {
        "scrape-all-users": {
            "task": "app.worker.scrape_all_users",
            "schedule": timedelta(hours=2),  # Run every 2 hours
        },
    }

    celery_app.conf.timezone = "UTC"

if __name__ == "__main__":
    if USE_CELERY and celery_app:
        celery_app.start()
    else:
        logger.error(
            "Celery not available. Use 'python -c \"from backend.worker import "
            "sync_scrape_all_users; sync_scrape_all_users()\"' for manual "
            "scraping"
        )
