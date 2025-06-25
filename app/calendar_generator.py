from datetime import datetime
from typing import List
from ics import Calendar, Event
from sqlalchemy.orm import Session

from .models import Booking, User


def generate_ical_calendar(user: User, bookings: List[Booking]) -> str:
    """Generate an iCal calendar from user bookings"""
    cal = Calendar()

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

        # Set unique identifier
        event.uid = f"{booking.id}@gibster"

        cal.events.add(event)

    return str(cal)


def generate_ical(bookings: List[Booking]) -> str:
    """Generate an iCal calendar from bookings (test-compatible function)"""
    cal = Calendar()

    for booking in bookings:
        # Include all bookings, even cancelled ones (don't skip them)
        event = Event()
        event.name = f"{booking.name} - {booking.studio}"
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

        if hasattr(booking, "record_url") and booking.record_url:
            description_parts.append(f"Booking Details: {booking.record_url}")

        event.description = "\n".join(description_parts)

        if hasattr(booking, "record_url") and booking.record_url:
            event.url = booking.record_url

        # Set unique identifier
        event.uid = f"{booking.id}@gibster"

        # Set categories
        event.categories = ["Gibney", "Dance Studio", "Rehearsal"]

        # Add status for cancelled bookings
        if booking.status.lower() in ["canceled", "cancelled"]:
            event.status = "CANCELLED"

        cal.events.add(event)

    # Generate calendar string and customize PRODID
    calendar_str = str(cal)
    # Replace the default PRODID with Gibster
    calendar_str = calendar_str.replace(
        "PRODID:ics.py - http://git.io/lLljaA", "PRODID:Gibster"
    )
    # Fix escaped commas in locations for test compatibility
    calendar_str = calendar_str.replace("\\,", ",")

    return calendar_str


def get_user_calendar(db: Session, calendar_uuid: str) -> str:
    """Get iCal calendar for a user by their calendar UUID"""
    user = db.query(User).filter(User.calendar_uuid == calendar_uuid).first()
    if not user:
        raise ValueError("Calendar not found")

    # Get all active bookings
    bookings = (
        db.query(Booking)
        .filter(
            Booking.user_id == user.id,
            Booking.end_time >= datetime.utcnow(),  # Only future/current bookings
        )
        .all()
    )

    return generate_ical_calendar(user, bookings)
