import os
import platform
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, cast
from uuid import UUID

from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
    Request,
    Response,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordRequestForm,
)
from sqlalchemy.orm import Session

from auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    decrypt_credential,
    encrypt_credential,
    get_password_hash,
    verify_password,
    verify_token,
)
from calendar_generator import get_user_calendar
from database import engine, get_db
from logging_config import get_logger, set_request_id, setup_logging
from models import Base, Booking, SyncJob, SyncJobLog, User
from schemas import (
    BookingResponse,
    CalendarUrl,
    SyncJobLogResponse,
    SyncJobLogsResponse,
    SyncJobResponse,
    SyncStartResponse,
    SyncStatusResponse,
    Token,
    UserCreate,
    UserCredentials,
    UserResponse,
)
from scraper import scrape_user_bookings
from worker import USE_CELERY, sync_scrape_user_with_job_tracking

# Setup logging
setup_logging()
logger = get_logger("main")


def mask_sensitive_value(value: str, visible_chars: int = 4) -> str:
    """Mask sensitive values for logging, showing only first and last few characters"""
    if not value or len(value) <= visible_chars * 2:
        return "***"
    return f"{value[:visible_chars]}...{value[-visible_chars:]}"


def get_safe_database_url(url: str) -> str:
    """Extract safe database URL for logging (no passwords)"""
    if not url:
        return "Not configured"

    # Handle SQLite
    if "sqlite" in url:
        return url

    # Handle PostgreSQL/MySQL etc
    try:
        # Simple regex to remove password
        import re

        # Match pattern: //username:password@host
        pattern = r"://([^:]+):([^@]+)@"
        replacement = r"://\1:***@"
        return re.sub(pattern, replacement, url)
    except:
        return mask_sensitive_value(url)


def log_configuration_summary():
    """Log application configuration summary at startup"""
    config_info = {
        "service": "gibster-backend",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "python_version": sys.version.split()[0],
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "configuration": {
            "database_url": get_safe_database_url(os.getenv("DATABASE_URL", "")),
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
            "app_host": os.getenv("APP_HOST", "0.0.0.0"),
            "app_port": os.getenv("APP_PORT", "8000"),
            "frontend_base_url": os.getenv("FRONTEND_BASE_URL", "Not set"),
            "celery_enabled": USE_CELERY,
            "redis_host": os.getenv("REDIS_HOST", "Not set") if USE_CELERY else "N/A",
            "redis_port": os.getenv("REDIS_PORT", "6379") if USE_CELERY else "N/A",
            "auth_token_expire_minutes": ACCESS_TOKEN_EXPIRE_MINUTES,
        },
        "security": {
            "secret_key_configured": bool(os.getenv("SECRET_KEY")),
            "encryption_key_configured": bool(os.getenv("ENCRYPTION_KEY")),
        },
    }

    logger.info("=" * 60)
    logger.info("GIBSTER BACKEND CONFIGURATION")
    logger.info("=" * 60)
    for key, value in config_info.items():
        if isinstance(value, dict):
            logger.info(f"{key.upper()}:")
            for sub_key, sub_value in value.items():
                logger.info(f"  {sub_key}: {sub_value}")
        else:
            logger.info(f"{key.upper()}: {value}")
    logger.info("=" * 60)


# Log configuration summary
log_configuration_summary()

# Create database tables
logger.info("Creating database tables")
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
except Exception as e:
    logger.error(f"Failed to create database tables: {e}")
    raise

app = FastAPI(
    title="Gibster",
    description=(
        "A service to synchronize Gibney dance space bookings "
        "with personal calendars"
    ),
    version="1.0.0",
)

# CORS middleware
logger.info("Configuring CORS middleware")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer(auto_error=False)


# Helper function for background sync tasks
def run_sync_task_in_background(user_id: str, job_id: str):
    """Wrapper function to run sync task in background for non-Celery environments"""
    import asyncio

    from .database import SessionLocal

    logger.info(f"Starting background sync task for user {user_id}, job {job_id}")

    # Create a new database session for the background task
    db = SessionLocal()
    try:
        # Convert string IDs to UUID objects
        user_uuid = UUID(user_id)

        # Get user from database
        user = db.query(User).filter(User.id == user_uuid).first()
        if not user:
            logger.error(f"User {user_id} not found in background task")
            return

        # Convert job_id to UUID
        job_uuid = UUID(job_id)

        # Create new event loop for the thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Run the async function
        loop.run_until_complete(sync_scrape_user_with_job_tracking(db, user, job_uuid))

        logger.info(f"Background sync task completed for user {user_id}, job {job_id}")

    except Exception as e:
        logger.error(
            f"Background sync task failed for user {user_id}: {e}", exc_info=True
        )
        # Try to update job status to failed
        try:
            job_uuid = UUID(job_id)
            job = db.query(SyncJob).filter(SyncJob.id == job_uuid).first()
            if job:
                setattr(job, "status", "failed")
                setattr(job, "error_message", f"Background task error: {str(e)}")
                setattr(job, "completed_at", datetime.now(timezone.utc))
                setattr(job, "last_updated_at", datetime.now(timezone.utc))
                db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update job status: {db_error}")
    finally:
        db.close()
        if "loop" in locals():
            loop.close()


# Request tracking middleware
@app.middleware("http")
async def request_tracking_middleware(request: Request, call_next):
    """Track requests with unique IDs and timing"""
    request_id = str(uuid.uuid4())
    set_request_id(request_id)

    start_time = time.time()

    # Only log non-health check requests in detail
    is_health_check = request.url.path in ["/", "/health", "/api/health"]

    # Log request start (only for non-health checks or slow requests)
    if not is_health_check:
        logger.debug(
            f"Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "client_ip": request.client.host if request.client else "unknown",
            },
        )

    try:
        response = await call_next(request)

        # Calculate response time
        response_time = time.time() - start_time

        # Log based on conditions: errors, slow requests, or important endpoints
        should_log = (
            response.status_code >= 400  # Log errors
            or response_time > 1.0  # Log slow requests (>1s)
            or request.method in ["POST", "PUT", "DELETE"]  # Log mutation operations
            or not is_health_check  # Log non-health check requests
        )

        # Add request ID to response headers for debugging
        response.headers["X-Request-ID"] = request_id

        return response

    except Exception as e:
        # Calculate response time for failed requests
        response_time = time.time() - start_time

        # Log request failure
        logger.error(
            f"Request failed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "error": str(e),
                "response_time_seconds": round(response_time, 3),
            },
        )
        raise


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Get current authenticated user"""
    logger.debug("Authenticating user")

    if credentials is None:
        logger.warning("Authentication failed: No credentials provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    email = verify_token(token)

    if email is None:
        logger.warning("Authentication failed: Invalid token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            logger.warning(f"Authentication failed: User not found for email {email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )

        logger.debug(f"User authenticated successfully: {email}")
        return user

    except Exception as e:
        logger.error(f"Database error during authentication: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication error",
        )


@app.get("/")
async def root():
    """Health check endpoint"""
    logger.info("Health check endpoint accessed")
    return {"message": "Gibster API is running", "version": "1.0.0"}


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint for Kubernetes probes"""
    try:
        # Test database connection
        from sqlalchemy import text

        db.execute(text("SELECT 1"))

        # Include configuration info for debugging
        config = {
            "environment": os.getenv("ENVIRONMENT", "development"),
            "celery_enabled": USE_CELERY,
            "database_type": "sqlite"
            if "sqlite" in os.getenv("DATABASE_URL", "")
            else "postgresql",
            "frontend_base_url_set": bool(os.getenv("FRONTEND_BASE_URL")),
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
        }

        return {
            "status": "healthy",
            "service": "gibster-api",
            "version": "1.0.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {"database": "ok"},
            "config": config,
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service unhealthy"
        )


@app.post("/api/v1/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Create a new Gibster user account"""
    logger.info(f"User registration attempt for email: {user_data.email}")

    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            logger.warning(
                f"Registration failed: Email already exists - {user_data.email}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Create new user
        logger.debug(f"Creating new user account for: {user_data.email}")
        hashed_password = get_password_hash(user_data.password)
        user = User(email=user_data.email, password_hash=hashed_password)

        db.add(user)
        db.commit()
        db.refresh(user)

        logger.info(f"User registered successfully: {user_data.email}")
        return user

    except HTTPException:
        # Re-raise HTTP exceptions as they are already handled
        raise
    except Exception as e:
        logger.error(f"Registration failed for {user_data.email}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        )


@app.post("/api/v1/auth/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """Log in and receive a JWT token"""
    logger.info(f"Login attempt for email: {form_data.username}")

    try:
        user = db.query(User).filter(User.email == form_data.username).first()

        if not user or not verify_password(
            form_data.password, cast(str, user.password_hash)
        ):
            logger.warning(
                f"Login failed: Invalid credentials for {form_data.username}"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )

        logger.info(f"User logged in successfully: {form_data.username}")
        return {"access_token": access_token, "token_type": "bearer"}

    except HTTPException:
        # Re-raise HTTP exceptions as they are already handled
        raise
    except Exception as e:
        logger.error(f"Login error for {form_data.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login failed"
        )


@app.get("/api/v1/user/credentials/email")
async def get_credentials_email(
    current_user: User = Depends(get_current_user),
):
    """Get the user's Gibney email (for form pre-population)"""
    logger.debug(f"Retrieving Gibney email for user: {current_user.email}")

    try:
        gibney_email = getattr(current_user, "gibney_email", None)
        if not gibney_email:
            logger.debug(f"No Gibney email found for user: {current_user.email}")
            return {"gibney_email": None}

        # Decrypt and return only the email
        decrypted_email = decrypt_credential(str(gibney_email))
        logger.debug(
            f"Gibney email retrieved successfully for user: {current_user.email}"
        )
        return {"gibney_email": decrypted_email}

    except Exception as e:
        logger.error(f"Failed to retrieve Gibney email for {current_user.email}: {e}")
        return {"gibney_email": None}


@app.put("/api/v1/user/credentials")
async def update_credentials(
    credentials: UserCredentials,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update Gibney email and password"""
    logger.info(f"Updating Gibney credentials for user: {current_user.email}")

    try:
        # Encrypt credentials before storing
        encrypted_email = encrypt_credential(credentials.gibney_email)
        encrypted_password = encrypt_credential(credentials.gibney_password)

        # Update user attributes
        setattr(current_user, "gibney_email", encrypted_email)
        setattr(current_user, "gibney_password", encrypted_password)
        setattr(current_user, "updated_at", datetime.now(timezone.utc))

        db.commit()

        logger.info(
            f"Gibney credentials updated successfully for user: {current_user.email}"
        )
        return {"message": "Credentials updated successfully"}

    except Exception as e:
        logger.error(f"Failed to update credentials for {current_user.email}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update credentials",
        )


@app.get("/api/v1/user/calendar_url", response_model=CalendarUrl)
async def get_calendar_url(
    request: Request, current_user: User = Depends(get_current_user)
):
    """Get the user's unique calendar subscription URL"""
    logger.debug(f"Generating calendar URL for user: {current_user.email}")

    try:
        # Check if FRONTEND_BASE_URL is configured
        frontend_base_url = os.getenv("FRONTEND_BASE_URL")

        if frontend_base_url:
            # Use frontend URL if configured
            base_url = frontend_base_url.rstrip("/")
            logger.debug(f"Using frontend base URL: {base_url}")
        else:
            # Fall back to request base URL (current behavior)
            base_url = str(request.base_url).rstrip("/")
            logger.debug(f"Using request base URL: {base_url}")

        calendar_uuid = cast(UUID, current_user.calendar_uuid)
        calendar_url = f"{base_url}/calendar/{calendar_uuid}.ics"

        logger.debug(
            f"Calendar URL generated for user: {current_user.email} - {calendar_url}"
        )
        return CalendarUrl(calendar_url=calendar_url, calendar_uuid=calendar_uuid)

    except Exception as e:
        logger.error(f"Failed to generate calendar URL for {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate calendar URL",
        )


@app.get("/api/v1/user/bookings", response_model=List[BookingResponse])
async def get_user_bookings(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get user's current bookings"""
    logger.debug(f"Retrieving bookings for user: {current_user.email}")

    try:
        bookings = db.query(Booking).filter(Booking.user_id == current_user.id).all()
        logger.info(
            f"Retrieved {len(bookings)} bookings for user: {current_user.email}"
        )
        return bookings

    except Exception as e:
        logger.error(f"Failed to retrieve bookings for {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve bookings",
        )


@app.post("/api/v1/user/sync", response_model=SyncStartResponse)
async def sync_bookings(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Manually trigger booking synchronization with progress tracking"""
    logger.info(f"Manual sync triggered by user: {current_user.email}")

    gibney_email = (
        cast(str, current_user.gibney_email)
        if getattr(current_user, "gibney_email", None)
        else None
    )
    gibney_password = (
        cast(str, current_user.gibney_password)
        if getattr(current_user, "gibney_password", None)
        else None
    )

    if not gibney_email or not gibney_password:
        logger.warning(
            f"Sync failed: Missing Gibney credentials for user {current_user.email}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gibney credentials not set. Please update your credentials first.",
        )

    try:
        # Check if there's already a running sync job for this user
        # Also clean up any stale jobs before checking
        from .worker import check_and_mark_stale_jobs

        check_and_mark_stale_jobs(db)

        existing_running_job = (
            db.query(SyncJob)
            .filter(
                SyncJob.user_id == current_user.id,
                SyncJob.status.in_(["pending", "running"]),
            )
            .first()
        )

        if existing_running_job:
            logger.warning(f"Sync already in progress for user: {current_user.email}")
            return SyncStartResponse(
                job_id=cast(UUID, existing_running_job.id),
                message="A sync is already in progress. Please wait for it to complete.",
                status=cast(str, existing_running_job.status) or "pending",
            )

        # Create a new sync job
        logger.debug(f"Creating sync job for user: {current_user.email}")
        sync_job = SyncJob(
            user_id=current_user.id,
            status="pending",
            progress="Initializing sync...",
            triggered_manually=True,
        )
        db.add(sync_job)
        db.commit()
        db.refresh(sync_job)

        logger.info(f"Sync job created: {sync_job.id} for user: {current_user.email}")

        if USE_CELERY:
            # If Celery is available, queue as background task
            logger.debug(f"Queueing sync job {sync_job.id} as background task")
            from .worker import scrape_user_task

            scrape_user_task.delay(str(current_user.id), str(sync_job.id))
        else:
            # Use FastAPI's BackgroundTasks for development
            logger.debug(f"Running sync job {sync_job.id} in background")
            background_tasks.add_task(
                run_sync_task_in_background, str(current_user.id), str(sync_job.id)
            )

        return SyncStartResponse(
            job_id=cast(UUID, sync_job.id),
            message="Sync started successfully",
            status=cast(str, sync_job.status) or "pending",
        )

    except Exception as e:
        logger.error(
            f"Failed to start sync for {current_user.email}: {e}", exc_info=True
        )
        db.rollback()

        # Try to create a failed job record for visibility
        try:
            failed_job = SyncJob(
                user_id=current_user.id,
                status="failed",
                progress="Failed to start sync",
                error_message=f"Failed to start sync: {str(e)}",
                triggered_manually=True,
                completed_at=datetime.now(timezone.utc),
            )
            db.add(failed_job)
            db.commit()
            logger.info(
                f"Created failed job record {failed_job.id} for error visibility"
            )
        except:
            logger.error("Failed to create error job record")
            db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start sync: {str(e)}",
        )


@app.get("/api/v1/user/sync/status", response_model=SyncStatusResponse)
async def get_sync_status(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get the current sync status for the user"""
    logger.debug(f"Retrieving sync status for user: {current_user.email}")

    try:
        # Get the most recent sync job for this user
        latest_job = (
            db.query(SyncJob)
            .filter(SyncJob.user_id == current_user.id)
            .order_by(SyncJob.started_at.desc())
            .first()
        )

        if not latest_job:
            logger.debug(f"No sync jobs found for user: {current_user.email}")
            # Create a default "no sync yet" job response
            import uuid
            from datetime import datetime

            default_job = SyncJobResponse(
                id=uuid.uuid4(),  # Generate a placeholder ID
                status="never_synced",
                progress="No sync has been performed yet",
                bookings_synced=0,
                error_message=None,
                started_at=datetime.now(timezone.utc),
                completed_at=None,
                triggered_manually=False,
            )
            return SyncStatusResponse(
                job=default_job,
                last_sync_at=getattr(current_user, "last_sync_at", None),
            )

        logger.debug(
            f"Latest sync job found: {latest_job.id} for user: {current_user.email}"
        )
        return SyncStatusResponse(
            job=SyncJobResponse(
                id=cast(UUID, latest_job.id),
                status=cast(str, latest_job.status) or "unknown",
                progress=(
                    cast(str, latest_job.progress)
                    if getattr(latest_job, "progress", None) is not None
                    else "No progress information"
                ),
                bookings_synced=int(
                    cast(int, latest_job.bookings_synced)
                    if getattr(latest_job, "bookings_synced", None) is not None
                    else 0
                ),
                error_message=(
                    cast(str, latest_job.error_message)
                    if getattr(latest_job, "error_message", None) is not None
                    else None
                ),
                started_at=latest_job.started_at,  # type: ignore
                completed_at=(
                    latest_job.completed_at  # type: ignore
                    if getattr(latest_job, "completed_at", None) is not None
                    else None
                ),
                triggered_manually=(
                    cast(bool, latest_job.triggered_manually)
                    if getattr(latest_job, "triggered_manually", None) is not None
                    else False
                ),
            ),
            last_sync_at=getattr(current_user, "last_sync_at", None),
        )

    except Exception as e:
        logger.error(f"Failed to retrieve sync status for {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sync status",
        )


@app.get("/api/v1/user/sync/history")
async def get_sync_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 10,
):
    """Get sync history for the user"""
    logger.debug(
        f"Retrieving sync history for user: {current_user.email} (limit: {limit})"
    )

    try:
        jobs = (
            db.query(SyncJob)
            .filter(SyncJob.user_id == current_user.id)
            .order_by(SyncJob.started_at.desc())
            .limit(limit)
            .all()
        )

        logger.info(f"Retrieved {len(jobs)} sync jobs for user: {current_user.email}")

        return {
            "jobs": [
                SyncJobResponse(
                    id=cast(UUID, job.id),
                    status=cast(str, job.status) or "unknown",
                    progress=(
                        cast(str, job.progress)
                        if getattr(job, "progress", None) is not None
                        else "No progress information"
                    ),
                    bookings_synced=int(
                        cast(int, job.bookings_synced)
                        if getattr(job, "bookings_synced", None) is not None
                        else 0
                    ),
                    error_message=(
                        cast(str, job.error_message)
                        if getattr(job, "error_message", None) is not None
                        else None
                    ),
                    started_at=job.started_at,  # type: ignore
                    completed_at=(
                        job.completed_at  # type: ignore
                        if getattr(job, "completed_at", None) is not None
                        else None
                    ),
                    triggered_manually=(
                        cast(bool, job.triggered_manually)
                        if getattr(job, "triggered_manually", None) is not None
                        else False
                    ),
                )
                for job in jobs
            ]
        }

    except Exception as e:
        logger.error(f"Failed to retrieve sync history for {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sync history",
        )


@app.get("/calendar/{calendar_uuid}.ics")
async def get_calendar_feed(calendar_uuid: str, db: Session = Depends(get_db)):
    """Public endpoint to serve the iCal file"""
    logger.info(f"Calendar feed requested for UUID: {calendar_uuid}")

    try:
        calendar_content = get_user_calendar(db, calendar_uuid)

        logger.info(f"Calendar feed generated successfully for UUID: {calendar_uuid}")
        return Response(
            content=calendar_content,
            media_type="text/calendar",
            headers={
                "Content-Disposition": (
                    f"inline; filename=gibney-bookings-{calendar_uuid}.ics"
                ),
                # Allow caching for 2 hours to reduce server load
                "Cache-Control": "public, max-age=7200",
                "X-WR-CALNAME": "Gibney Bookings",
                # Support both https and webcal protocols
                "Access-Control-Allow-Origin": "*",
            },
        )

    except ValueError as e:
        logger.warning(f"Calendar not found for UUID: {calendar_uuid} - {e}")
        # Handle invalid UUID or calendar not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar not found",
        )
    except Exception as e:
        logger.error(f"Failed to generate calendar for UUID {calendar_uuid}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate calendar",
        )


@app.get("/api/v1/user/sync/job/{job_id}/logs", response_model=SyncJobLogsResponse)
async def get_sync_job_logs(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = 1,
    limit: int = 100,
    level: Optional[str] = None,
):
    """Get logs for a specific sync job"""
    logger.debug(
        f"Retrieving logs for sync job {job_id} requested by {current_user.email}"
    )

    try:
        # Verify the job belongs to the user
        job = (
            db.query(SyncJob)
            .filter(SyncJob.id == job_id, SyncJob.user_id == current_user.id)
            .first()
        )

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Sync job not found"
            )

        # Build query for logs
        query = db.query(SyncJobLog).filter(SyncJobLog.sync_job_id == job_id)

        # Filter by level if specified
        if level:
            query = query.filter(SyncJobLog.level == level.upper())

        # Order by timestamp
        query = query.order_by(SyncJobLog.timestamp.desc())

        # Get total count
        total = query.count()

        # Pagination
        offset = (page - 1) * limit
        logs = query.offset(offset).limit(limit).all()

        return SyncJobLogsResponse(
            logs=[
                SyncJobLogResponse(
                    id=cast(UUID, log.id),
                    sync_job_id=cast(UUID, log.sync_job_id),
                    timestamp=log.timestamp,  # type: ignore
                    level=cast(str, log.level),
                    message=cast(str, log.message),
                    details=cast(Dict[str, Any], log.details) if log.details else {},
                )
                for log in logs
            ],
            total=total,
            page=page,
            limit=limit,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve sync job logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sync job logs",
        )


@app.get("/api/v1/user/profile", response_model=UserResponse)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    logger.debug(f"User profile requested for: {current_user.email}")
    return current_user


@app.post("/api/v1/admin/cleanup-sync-jobs")
async def cleanup_sync_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days_to_keep: int = 30,
):
    """Manually trigger cleanup of old sync jobs (admin only)"""
    logger.info(f"Manual sync job cleanup requested by user: {current_user.email}")

    try:
        from .worker import check_and_mark_stale_jobs, cleanup_old_sync_jobs

        # Check for stale jobs
        stale_count = check_and_mark_stale_jobs(db)

        # Clean up old jobs
        cleaned_count = cleanup_old_sync_jobs(db, days_to_keep)

        logger.info(
            f"Cleanup completed: {stale_count} stale jobs marked, {cleaned_count} old jobs cleaned"
        )

        return {
            "message": "Cleanup completed successfully",
            "stale_jobs_marked": stale_count,
            "old_jobs_cleaned": cleaned_count,
            "days_kept": days_to_keep,
        }

    except Exception as e:
        logger.error(f"Failed to cleanup sync jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup sync jobs",
        )


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting Gibster API server")
    uvicorn.run(app, host="0.0.0.0", port=8000)
