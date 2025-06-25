from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.auth import get_password_hash
from app.models import Booking, User


@pytest.mark.unit
class TestUserModel:
    """Test User model functionality"""

    def test_create_user(self, test_db):
        """Test creating a user"""
        user = User(
            email="test@example.com", password_hash=get_password_hash("password123")
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)

        assert user.id is not None
        assert str(user.email) == "test@example.com"
        assert user.calendar_uuid is not None
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_user_email_unique(self, test_db):
        """Test that user emails must be unique"""
        # Create first user
        user1 = User(
            email="test@example.com", password_hash=get_password_hash("password123")
        )
        test_db.add(user1)
        test_db.commit()

        # Try to create second user with same email
        user2 = User(
            email="test@example.com", password_hash=get_password_hash("password456")
        )
        test_db.add(user2)

        with pytest.raises(IntegrityError):
            test_db.commit()

    def test_user_calendar_uuid_unique(self, test_db):
        """Test that calendar UUIDs are unique"""
        user1 = User(
            email="test1@example.com", password_hash=get_password_hash("password123")
        )
        user2 = User(
            email="test2@example.com", password_hash=get_password_hash("password456")
        )

        test_db.add(user1)
        test_db.add(user2)
        test_db.commit()
        test_db.refresh(user1)
        test_db.refresh(user2)

        assert str(user1.calendar_uuid) != str(user2.calendar_uuid)

    def test_user_repr(self, test_db):
        """Test user string representation"""
        user = User(
            email="test@example.com", password_hash=get_password_hash("password123")
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)

        assert str(user) == f"<User {user.email}>"


@pytest.mark.unit
class TestBookingModel:
    """Test Booking model functionality"""

    def test_create_booking(self, test_db):
        """Test creating a booking"""
        # First create a user
        user = User(
            email="test@example.com", password_hash=get_password_hash("password123")
        )
        test_db.add(user)
        test_db.commit()

        # Create booking
        booking = Booking(
            id="test-booking-1",
            user_id=user.id,
            name="R-490015",
            start_time=datetime(2024, 1, 15, 10, 0),
            end_time=datetime(2024, 1, 15, 12, 0),
            studio="Studio A",
            location="280 Broadway",
            status="Confirmed",
            price=50.00,
            record_url="https://gibney.my.site.com/s/rental-form?Id=test-booking-1",
        )
        test_db.add(booking)
        test_db.commit()
        test_db.refresh(booking)

        assert str(booking.id) == "test-booking-1"
        assert str(booking.user_id) == str(user.id)
        assert str(booking.name) == "R-490015"
        assert str(booking.studio) == "Studio A"
        assert str(booking.price) == "50.00"
        assert booking.last_seen is not None

    def test_booking_user_relationship(self, test_db):
        """Test booking-user relationship"""
        # Create user
        user = User(
            email="test@example.com", password_hash=get_password_hash("password123")
        )
        test_db.add(user)
        test_db.commit()

        # Create booking
        booking = Booking(
            id="test-booking-1",
            user_id=user.id,
            name="R-490015",
            start_time=datetime(2024, 1, 15, 10, 0),
            end_time=datetime(2024, 1, 15, 12, 0),
            studio="Studio A",
            location="280 Broadway",
            status="Confirmed",
            price=50.00,
            record_url="https://gibney.my.site.com/s/rental-form?Id=test-booking-1",
        )
        test_db.add(booking)
        test_db.commit()

        # Test relationship
        assert booking.user == user
        assert booking in user.bookings

    def test_booking_id_unique(self, test_db):
        """Test that booking IDs must be unique"""
        # Create user
        user = User(
            email="test@example.com", password_hash=get_password_hash("password123")
        )
        test_db.add(user)
        test_db.commit()

        # Create first booking
        booking1 = Booking(
            id="duplicate-id",
            user_id=user.id,
            name="R-490015",
            start_time=datetime(2024, 1, 15, 10, 0),
            end_time=datetime(2024, 1, 15, 12, 0),
            studio="Studio A",
            location="280 Broadway",
            status="Confirmed",
            price=50.00,
            record_url="https://gibney.my.site.com/s/rental-form?Id=duplicate-id",
        )
        test_db.add(booking1)
        test_db.commit()

        # Try to create second booking with same ID
        booking2 = Booking(
            id="duplicate-id",
            user_id=user.id,
            name="R-490016",
            start_time=datetime(2024, 1, 16, 10, 0),
            end_time=datetime(2024, 1, 16, 12, 0),
            studio="Studio B",
            location="890 Broadway",
            status="Confirmed",
            price=75.00,
            record_url="https://gibney.my.site.com/s/rental-form?Id=duplicate-id",
        )
        test_db.add(booking2)

        with pytest.raises(IntegrityError):
            test_db.commit()

    def test_multiple_bookings_per_user(self, test_db):
        """Test that a user can have multiple bookings"""
        # Create user
        user = User(
            email="test@example.com", password_hash=get_password_hash("password123")
        )
        test_db.add(user)
        test_db.commit()

        # Create multiple bookings
        booking1 = Booking(
            id="booking-1",
            user_id=user.id,
            name="R-490015",
            start_time=datetime(2024, 1, 15, 10, 0),
            end_time=datetime(2024, 1, 15, 12, 0),
            studio="Studio A",
            location="280 Broadway",
            status="Confirmed",
            price=50.00,
            record_url="https://gibney.my.site.com/s/rental-form?Id=booking-1",
        )

        booking2 = Booking(
            id="booking-2",
            user_id=user.id,
            name="R-490016",
            start_time=datetime(2024, 1, 16, 14, 0),
            end_time=datetime(2024, 1, 16, 16, 0),
            studio="Studio B",
            location="890 Broadway",
            status="Confirmed",
            price=75.00,
            record_url="https://gibney.my.site.com/s/rental-form?Id=booking-2",
        )

        test_db.add(booking1)
        test_db.add(booking2)
        test_db.commit()

        # Verify both bookings exist and belong to user
        assert len(user.bookings) == 2
        assert booking1 in user.bookings
        assert booking2 in user.bookings

    def test_booking_repr(self, test_db):
        """Test booking string representation"""
        # Create user
        user = User(
            email="test@example.com", password_hash=get_password_hash("password123")
        )
        test_db.add(user)
        test_db.commit()

        # Create booking
        booking = Booking(
            id="test-booking-1",
            user_id=user.id,
            name="R-490015",
            start_time=datetime(2024, 1, 15, 10, 0),
            end_time=datetime(2024, 1, 15, 12, 0),
            studio="Studio A",
            location="280 Broadway",
            status="Confirmed",
            price=50.00,
            record_url="https://gibney.my.site.com/s/rental-form?Id=test-booking-1",
        )
        test_db.add(booking)
        test_db.commit()

        assert str(booking) == f"<Booking {booking.name} - {booking.studio}>"

    def test_booking_with_minimal_data(self, test_db):
        """Test creating booking with only required fields"""
        # Create user
        user = User(
            email="test@example.com", password_hash=get_password_hash("password123")
        )
        test_db.add(user)
        test_db.commit()

        # Create booking with minimal data
        booking = Booking(
            id="minimal-booking",
            user_id=user.id,
            name="R-490015",
            start_time=datetime(2024, 1, 15, 10, 0),
            end_time=datetime(2024, 1, 15, 12, 0),
            studio="Studio A",
            location="280 Broadway",
            status="Confirmed",
            # price and record_url can be None/optional
        )
        test_db.add(booking)
        test_db.commit()

        assert str(booking.id) == "minimal-booking"
        assert booking.price is None
        assert booking.record_url is None
