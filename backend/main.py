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
from .models import Base, Booking, User
from .schemas import (
    BookingResponse,
    CalendarUrl,
    Token,
    UserCreate,
    UserCredentials,
    UserResponse,
)
from .scraper import scrape_user_bookings

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Gibster",
    description=(
        "A service to synchronize Gibney dance space bookings "
        "with personal calendars"
    ),
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Get current authenticated user"""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    email = verify_token(token)

    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    return user


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Gibster API is running", "version": "1.0.0"}


@app.post("/api/v1/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Create a new Gibster user account"""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user = User(email=user_data.email, password_hash=hashed_password)

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@app.post("/api/v1/auth/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """Log in and receive a JWT token"""
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not verify_password(
        form_data.password, cast(str, user.password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/v1/user/credentials/email")
async def get_credentials_email(
    current_user: User = Depends(get_current_user),
):
    """Get the user's Gibney email (for form pre-population)"""
    try:
        gibney_email = getattr(current_user, "gibney_email", None)
        if not gibney_email:
            return {"gibney_email": None}

        # Decrypt and return only the email
        decrypted_email = decrypt_credential(str(gibney_email))
        return {"gibney_email": decrypted_email}

    except Exception:
        return {"gibney_email": None}


@app.put("/api/v1/user/credentials")
async def update_credentials(
    credentials: UserCredentials,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update Gibney email and password"""
    try:
        # Encrypt credentials before storing
        encrypted_email = encrypt_credential(credentials.gibney_email)
        encrypted_password = encrypt_credential(credentials.gibney_password)

        # Update user attributes
        setattr(current_user, "gibney_email", encrypted_email)
        setattr(current_user, "gibney_password", encrypted_password)
        setattr(current_user, "updated_at", datetime.utcnow())

        db.commit()

        return {"message": "Credentials updated successfully"}

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update credentials",
        )


@app.get("/api/v1/user/calendar_url", response_model=CalendarUrl)
async def get_calendar_url(
    request: Request, current_user: User = Depends(get_current_user)
):
    """Get the user's unique calendar subscription URL"""
    base_url = str(request.base_url).rstrip("/")
    calendar_uuid = cast(uuid.UUID, current_user.calendar_uuid)
    calendar_url = f"{base_url}/calendar/{calendar_uuid}.ics"

    return CalendarUrl(calendar_url=calendar_url, calendar_uuid=calendar_uuid)


@app.get("/api/v1/user/bookings", response_model=List[BookingResponse])
async def get_user_bookings(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get user's current bookings"""
    bookings = db.query(Booking).filter(Booking.user_id == current_user.id).all()
    return bookings


@app.post("/api/v1/user/sync")
async def sync_bookings(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Manually trigger booking synchronization"""
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gibney credentials not set. Please update your credentials first.",
        )

    try:
        # For local development without Celery, run synchronously
        from .worker import USE_CELERY

        if USE_CELERY:
            # If Celery is available, you could queue this as a background task
            # For now, we'll still run it synchronously for immediate feedback
            pass

        updated_bookings = scrape_user_bookings(db, current_user)
        return {
            "message": f"Successfully synchronized {len(updated_bookings)} bookings",
            "bookings_count": len(updated_bookings),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync bookings: {str(e)}",
        )


@app.get("/calendar/{calendar_uuid}.ics")
async def get_calendar_feed(calendar_uuid: str, db: Session = Depends(get_db)):
    """Public endpoint to serve the iCal file"""
    try:
        calendar_content = get_user_calendar(db, calendar_uuid)

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

    except ValueError:
        # Handle invalid UUID or calendar not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar not found",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate calendar",
        )


@app.get("/api/v1/user/profile", response_model=UserResponse)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return current_user


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
