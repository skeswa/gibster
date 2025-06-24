import pytest
from datetime import datetime
from app.calendar_generator import generate_ical_calendar
from app.models import Booking, User


@pytest.mark.unit
class TestCalendarGeneration:
    """Test iCal calendar generation"""

    def test_generate_ical_empty_bookings(self):
        """Test calendar generation with no bookings"""
        user = User(id=1, email="test@example.com")
        calendar_str = generate_ical_calendar(user, [])

        assert "BEGIN:VCALENDAR" in calendar_str
        assert "END:VCALENDAR" in calendar_str
        assert "VERSION:2.0" in calendar_str
        assert "PRODID" in calendar_str
        # Should not contain any events
        assert "BEGIN:VEVENT" not in calendar_str

    def test_generate_ical_single_booking(self):
        """Test calendar generation with single booking"""
        user = User(id=1, email="test@example.com")

        # Create a test booking
        booking = Booking(
            id="test-booking-1",
            user_id=1,
            name="R-490015",
            start_time=datetime(2024, 1, 15, 10, 0),
            end_time=datetime(2024, 1, 15, 12, 0),
            studio="Studio A",
            location="280 Broadway",
            status="Confirmed",
            price=50.00,
            record_url="https://gibney.my.site.com/s/rental-form?Id=test-booking-1",
        )

        calendar_str = generate_ical_calendar(user, [booking])

        # Check calendar structure
        assert "BEGIN:VCALENDAR" in calendar_str
        assert "END:VCALENDAR" in calendar_str
        assert "VERSION:2.0" in calendar_str

        # Check event content
        assert "BEGIN:VEVENT" in calendar_str
        assert "END:VEVENT" in calendar_str
        assert "Studio A at 280 Broadway" in calendar_str
        assert (
            "Studio A\\, 280 Broadway" in calendar_str
        )  # Comma is escaped in iCal format
        assert "test-booking-1" in calendar_str

    def test_generate_ical_multiple_bookings(self):
        """Test calendar generation with multiple bookings"""
        user = User(id=1, email="test@example.com")

        bookings = [
            Booking(
                id="test-booking-1",
                user_id=1,
                name="R-490015",
                start_time=datetime(2024, 1, 15, 10, 0),
                end_time=datetime(2024, 1, 15, 12, 0),
                studio="Studio A",
                location="280 Broadway",
                status="Confirmed",
                price=50.00,
                record_url="https://gibney.my.site.com/s/rental-form?Id=test-booking-1",
            ),
            Booking(
                id="test-booking-2",
                user_id=1,
                name="R-490016",
                start_time=datetime(2024, 1, 16, 14, 0),
                end_time=datetime(2024, 1, 16, 16, 0),
                studio="Studio B",
                location="890 Broadway",
                status="Confirmed",
                price=75.00,
                record_url="https://gibney.my.site.com/s/rental-form?Id=test-booking-2",
            ),
        ]

        calendar_str = generate_ical_calendar(user, bookings)

        # Should contain both events
        assert calendar_str.count("BEGIN:VEVENT") == 2
        assert calendar_str.count("END:VEVENT") == 2
        assert "Studio A at 280 Broadway" in calendar_str
        assert "Studio B at 890 Broadway" in calendar_str
        assert "280 Broadway" in calendar_str
        assert "890 Broadway" in calendar_str

    def test_generate_ical_special_characters(self):
        """Test calendar generation with special characters in booking data"""
        user = User(id=1, email="test@example.com")

        booking = Booking(
            id="test-booking-special",
            user_id=1,
            name="R-490015 (Special Event)",
            start_time=datetime(2024, 1, 15, 10, 0),
            end_time=datetime(2024, 1, 15, 12, 0),
            studio="Studio A & B",
            location="280 Broadway, NYC",
            status="Confirmed",
            price=50.00,
            record_url="https://gibney.my.site.com/s/rental-form?Id=test-booking-special",
        )

        calendar_str = generate_ical_calendar(user, [booking])

        # Should handle special characters properly
        assert "BEGIN:VEVENT" in calendar_str
        assert "SUMMARY:" in calendar_str
        assert "LOCATION:" in calendar_str

    def test_generate_ical_cancelled_booking(self):
        """Test calendar generation with cancelled booking"""
        user = User(id=1, email="test@example.com")

        booking = Booking(
            id="test-booking-cancelled",
            user_id=1,
            name="R-490015",
            start_time=datetime(2024, 1, 15, 10, 0),
            end_time=datetime(2024, 1, 15, 12, 0),
            studio="Studio A",
            location="280 Broadway",
            status="canceled",
            price=50.00,
            record_url="https://gibney.my.site.com/s/rental-form?Id=test-booking-cancelled",
        )

        calendar_str = generate_ical_calendar(user, [booking])

        # Should skip cancelled bookings (as per the actual implementation)
        assert "BEGIN:VEVENT" not in calendar_str
