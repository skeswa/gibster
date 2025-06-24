from datetime import datetime
from typing import List
from ics import Calendar, Event
from sqlalchemy.orm import Session

from .models import Booking, User

def generate_ical_calendar(user: User, bookings: List[Booking]) -> str:
    """Generate an iCal calendar from user bookings"""
    cal = Calendar()
    cal.meta["VERSION"] = "2.0"
    cal.meta["PRODID"] = "-//Gibster//Gibney Booking Calendar//EN"
    cal.meta["CALSCALE"] = "GREGORIAN"
    cal.meta["METHOD"] = "PUBLISH"
    cal.meta["X-WR-CALNAME"] = f"Gibney Bookings - {user.email}"
    cal.meta["X-WR-CALDESC"] = "Your Gibney dance studio bookings"
    
    for booking in bookings:
        # Skip canceled bookings
        if booking.status.lower() == "canceled":
            continue
        
        event = Event()
        event.name = f"{booking.studio} at {booking.location}"
        event.begin = booking.start_time
        event.end = booking.end_time
        event.location = f"{booking.studio}, {booking.location}"
        
        # Build description
        description_parts = [
            f"Rental: {booking.name}",
            f"Studio: {booking.studio}",
            f"Location: {booking.location}",
            f"Status: {booking.status}",
        ]
        
        if booking.price:
            description_parts.append(f"Price: ${booking.price:.2f}")
        
        description_parts.append(f"Booking Details: {booking.record_url}")
        
        event.description = "\n".join(description_parts)
        event.url = booking.record_url
        
        # Set unique identifier
        event.uid = f"{booking.id}@gibster"
        
        # Set categories
        event.categories = ["Gibney", "Dance Studio", "Rehearsal"]
        
        cal.events.add(event)
    
    return str(cal)

def get_user_calendar(db: Session, calendar_uuid: str) -> str:
    """Get iCal calendar for a user by their calendar UUID"""
    user = db.query(User).filter(User.calendar_uuid == calendar_uuid).first()
    if not user:
        raise ValueError("Calendar not found")
    
    # Get all active bookings
    bookings = db.query(Booking).filter(
        Booking.user_id == user.id,
        Booking.end_time >= datetime.utcnow()  # Only future/current bookings
    ).all()
    
    return generate_ical_calendar(user, bookings) 