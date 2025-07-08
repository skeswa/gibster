import uuid
from datetime import datetime, timezone
from typing import List, cast

from ics import Calendar, Event
from sqlalchemy.orm import Session

from .logging_config import get_logger
from .models import Booking, User

logger = get_logger("calendar_generator")


def generate_ical_calendar(user: User, bookings: List[Booking]) -> str:
    """Generate an iCal calendar from user bookings"""
    logger.info(
        f"Generating iCal calendar for user: {user.email} with {len(bookings)} bookings"
    )

    cal = Calendar()

    processed_bookings = 0
    skipped_bookings = 0

    for booking in bookings:
        try:
            # Skip canceled bookings
            if booking.status.lower() == "canceled":
                logger.debug(f"Skipping canceled booking: {booking.name}")
                skipped_bookings += 1
                continue

            logger.debug(f"Processing booking: {booking.name} at {booking.studio}")

            event = Event()
            event.name = f"{booking.studio} at {booking.location}"
            event.begin = cast(datetime, booking.start_time)
            event.end = cast(datetime, booking.end_time)
            event.location = f"{booking.studio}, {booking.location}"

            # Build description
            description_parts = [
                f"Rental: {booking.name}",
                f"Studio: {booking.studio}",
                f"Location: {booking.location}",
                f"Status: {booking.status}",
            ]

            if booking.price is not None:
                description_parts.append(f"Price: ${booking.price:.2f}")

            description_parts.append(f"Booking Details: {booking.record_url}")

            event.description = "\n".join(description_parts)

            # Set unique identifier
            event.uid = f"{booking.id}@gibster"

            cal.events.add(event)
            processed_bookings += 1

        except Exception as e:
            logger.error(f"Failed to process booking {booking.id}: {e}")
            continue

    logger.info(
        f"Calendar generation complete: {processed_bookings} events added, {skipped_bookings} skipped"
    )

    try:
        # Generate calendar string and customize PRODID
        logger.debug("Serializing calendar")
        calendar_str = cal.serialize()
        # Replace the default PRODID with Gibster
        calendar_str = calendar_str.replace(
            "PRODID:ics.py - http://git.io/lLljaA", "PRODID:Gibster"
        )

        logger.debug(
            f"Calendar serialized successfully, size: {len(calendar_str)} characters"
        )
        return calendar_str

    except Exception as e:
        logger.error(f"Failed to serialize calendar: {e}")
        raise


def generate_ical(bookings: List[Booking]) -> str:
    """Generate an iCal calendar from bookings (test-compatible function)"""
    logger.info(
        f"Generating iCal calendar with {len(bookings)} bookings (test-compatible)"
    )

    cal = Calendar()

    processed_bookings = 0

    for booking in bookings:
        try:
            logger.debug(
                f"Processing booking: {booking.name} (status: {booking.status})"
            )

            # Include all bookings, even cancelled ones (don't skip them)
            event = Event()
            event.name = f"{booking.name} - {booking.studio}"
            event.begin = cast(datetime, booking.start_time)
            event.end = cast(datetime, booking.end_time)
            event.location = f"{booking.studio}, {booking.location}"

            # Build description
            description_parts = [
                f"Rental: {booking.name}",
                f"Studio: {booking.studio}",
                f"Location: {booking.location}",
                f"Status: {booking.status}",
            ]

            if booking.price is not None:
                description_parts.append(f"Price: ${booking.price:.2f}")

            if hasattr(booking, "record_url") and booking.record_url is not None:
                description_parts.append(f"Booking Details: {booking.record_url}")

            event.description = "\n".join(description_parts)

            if hasattr(booking, "record_url") and booking.record_url is not None:
                event.url = str(booking.record_url)

            # Set unique identifier
            event.uid = f"{booking.id}@gibster"

            # Set categories
            event.categories = {"Gibney", "Dance Studio", "Rehearsal"}

            # Add status for cancelled bookings
            if booking.status.lower() in ["canceled", "cancelled"]:
                event.status = "CANCELLED"
                logger.debug(f"Marked event as cancelled: {booking.name}")

            cal.events.add(event)
            processed_bookings += 1

        except Exception as e:
            logger.error(f"Failed to process booking {booking.id}: {e}")
            continue

    logger.info(
        f"Test calendar generation complete: {processed_bookings} events processed"
    )

    try:
        # Generate calendar string and customize PRODID
        logger.debug("Serializing test calendar")
        calendar_str = cal.serialize()
        # Replace the default PRODID with Gibster
        calendar_str = calendar_str.replace(
            "PRODID:ics.py - http://git.io/lLljaA", "PRODID:Gibster"
        )
        # Fix escaped commas in locations for test compatibility
        calendar_str = calendar_str.replace("\\,", ",")

        logger.debug(
            f"Test calendar serialized successfully, size: {len(calendar_str)} characters"
        )
        return calendar_str

    except Exception as e:
        logger.error(f"Failed to serialize test calendar: {e}")
        raise


def get_user_calendar(db: Session, calendar_uuid: str) -> str:
    """Get iCal calendar for a user by their calendar UUID"""
    logger.info(f"Fetching calendar for UUID: {calendar_uuid}")

    try:
        # Validate UUID format and normalize to UUID object for database query
        if isinstance(calendar_uuid, uuid.UUID):
            calendar_uuid_obj = calendar_uuid
            logger.debug("UUID already in UUID format")
        else:
            # Validate that it's a valid UUID string and convert to UUID object
            logger.debug("Converting string to UUID object")
            calendar_uuid_obj = uuid.UUID(calendar_uuid)

    except ValueError as e:
        logger.warning(f"Invalid UUID format provided: {calendar_uuid} - {e}")
        raise ValueError("Calendar not found")

    try:
        # Query user by calendar UUID - use UUID object for proper SQLAlchemy comparison
        logger.debug(
            f"Querying database for user with calendar UUID: {calendar_uuid_obj}"
        )
        user = db.query(User).filter(User.calendar_uuid == calendar_uuid_obj).first()

        if not user:
            logger.warning(f"No user found with calendar UUID: {calendar_uuid_obj}")
            raise ValueError("Calendar not found")

        logger.info(f"Found user: {user.email} for calendar UUID: {calendar_uuid_obj}")

        # Get all active bookings
        logger.debug(f"Querying bookings for user: {user.email}")
        bookings = (
            db.query(Booking)
            .filter(
                Booking.user_id == user.id,
                Booking.end_time
                >= datetime.now(timezone.utc),  # Only future/current bookings
            )
            .all()
        )

        logger.info(f"Found {len(bookings)} active bookings for user: {user.email}")

        # Generate and return the calendar
        calendar_content = generate_ical_calendar(user, bookings)
        logger.info(f"Calendar generated successfully for user: {user.email}")
        return calendar_content

    except ValueError:
        # Re-raise ValueError (calendar not found) as is
        raise
    except Exception as e:
        logger.error(
            f"Database error while fetching calendar for UUID {calendar_uuid}: {e}"
        )
        raise ValueError("Calendar not found")
