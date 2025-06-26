import time
import uuid
from datetime import datetime, timedelta
from typing import List, cast

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordRequestForm,
)
from sqlalchemy.orm import Session

from .auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    decrypt_credential,
    encrypt_credential,
    get_password_hash,
    verify_password,
    verify_token,
)
from .calendar_generator import get_user_calendar
from .database import engine, get_db
from .logging_config import get_logger, set_request_id, setup_logging
from .models import Base, Booking, SyncJob, User
from .schemas import (
    BookingResponse,
    CalendarUrl,
    SyncJobResponse,
    SyncStartResponse,
    SyncStatusResponse,
    Token,
    UserCreate,
    UserCredentials,
    UserResponse,
)
from .scraper import scrape_user_bookings
from .worker import USE_CELERY, sync_scrape_user_with_job_tracking

# Setup logging
setup_logging()
logger = get_logger("main")

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


# Request tracking middleware
@app.middleware("http")
async def request_tracking_middleware(request: Request, call_next):
    """Track requests with unique IDs and timing"""
    request_id = str(uuid.uuid4())
    set_request_id(request_id)

    start_time = time.time()

    # Log request start
    logger.info(
        f"Request started",
        extra={
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown"),
        },
    )

    try:
        response = await call_next(request)

        # Calculate response time
        response_time = time.time() - start_time

        # Log successful response
        logger.info(
            f"Request completed",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "response_time_seconds": round(response_time, 3),
            },
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
        setattr(current_user, "updated_at", datetime.utcnow())

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
        base_url = str(request.base_url).rstrip("/")
        calendar_uuid = cast(uuid.UUID, current_user.calendar_uuid)
        calendar_url = f"{base_url}/calendar/{calendar_uuid}.ics"

        logger.debug(f"Calendar URL generated for user: {current_user.email}")
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
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
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
            # Run asynchronously for development
            logger.debug(f"Running sync job {sync_job.id} asynchronously")
            result = await sync_scrape_user_with_job_tracking(
                db, current_user, sync_job.id
            )

        return SyncStartResponse(
            job_id=sync_job.id,
            message="Sync started successfully",
            status=sync_job.status or "pending",
        )

    except Exception as e:
        logger.error(f"Failed to start sync for {current_user.email}: {e}")
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
                started_at=datetime.utcnow(),
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
                id=latest_job.id,
                status=latest_job.status or "unknown",
                progress=latest_job.progress or "No progress information",
                bookings_synced=int(latest_job.bookings_synced or 0),
                error_message=latest_job.error_message,
                started_at=latest_job.started_at,
                completed_at=latest_job.completed_at,
                triggered_manually=latest_job.triggered_manually or False,
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
                    id=job.id,
                    status=job.status or "unknown",
                    progress=job.progress or "No progress information",
                    bookings_synced=int(job.bookings_synced or 0),
                    error_message=job.error_message,
                    started_at=job.started_at,
                    completed_at=job.completed_at,
                    triggered_manually=job.triggered_manually or False,
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
                    f"attachment; filename=gibney-bookings-" f"{calendar_uuid}.ics"
                ),
                "Cache-Control": "no-cache, must-revalidate",
                "Pragma": "no-cache",
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


@app.get("/api/v1/user/profile", response_model=UserResponse)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    logger.debug(f"User profile requested for: {current_user.email}")
    return current_user


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting Gibster API server")
    uvicorn.run(app, host="0.0.0.0", port=8000)
