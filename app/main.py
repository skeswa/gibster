import os
from datetime import datetime, timedelta
from typing import List
from fastapi import FastAPI, Depends, HTTPException, status, Response, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import get_db, engine
from .models import Base, User, Booking
from .schemas import (
    UserCreate, UserCredentials, UserResponse, Token, 
    BookingResponse, CalendarUrl
)
from .auth import (
    verify_password, get_password_hash, create_access_token, 
    verify_token, encrypt_credential, ACCESS_TOKEN_EXPIRE_MINUTES
)
from .calendar_generator import get_user_calendar
from .scraper import scrape_user_bookings

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Gibster",
    description="A service to synchronize Gibney dance space bookings with personal calendars",
    version="1.0.0"
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
security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
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
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        password_hash=hashed_password
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user

@app.post("/api/v1/auth/token", response_model=Token)
async def login(user_data: UserCreate, db: Session = Depends(get_db)):
    """Log in and receive a JWT token"""
    user = db.query(User).filter(User.email == user_data.email).first()
    
    if not user or not verify_password(user_data.password, user.password_hash):
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

@app.put("/api/v1/user/credentials")
async def update_credentials(
    credentials: UserCredentials,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update Gibney email and password"""
    try:
        # Encrypt credentials before storing
        encrypted_email = encrypt_credential(credentials.gibney_email)
        encrypted_password = encrypt_credential(credentials.gibney_password)
        
        current_user.gibney_email = encrypted_email
        current_user.gibney_password = encrypted_password
        current_user.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {"message": "Credentials updated successfully"}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update credentials"
        )

@app.get("/api/v1/user/calendar_url", response_model=CalendarUrl)
async def get_calendar_url(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Get the user's unique calendar subscription URL"""
    base_url = str(request.base_url).rstrip('/')
    calendar_url = f"{base_url}/calendar/{current_user.calendar_uuid}.ics"
    
    return CalendarUrl(
        calendar_url=calendar_url,
        calendar_uuid=current_user.calendar_uuid
    )

@app.get("/api/v1/user/bookings", response_model=List[BookingResponse])
async def get_user_bookings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's current bookings"""
    bookings = db.query(Booking).filter(Booking.user_id == current_user.id).all()
    return bookings

@app.post("/api/v1/user/sync")
async def sync_bookings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually trigger booking synchronization"""
    if not current_user.gibney_email or not current_user.gibney_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gibney credentials not set. Please update your credentials first."
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
            "bookings_count": len(updated_bookings)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync bookings: {str(e)}"
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
                "Content-Disposition": f"attachment; filename=gibney-bookings-{calendar_uuid}.ics",
                "Cache-Control": "no-cache, must-revalidate",
                "Pragma": "no-cache"
            }
        )
    
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate calendar"
        )

@app.get("/api/v1/user/profile", response_model=UserResponse)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return current_user

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 