import pytest
from datetime import datetime
from app.calendar_generator import generate_ical
from app.models import Booking


@pytest.mark.unit
class TestCalendarGeneration:
    """Test iCal calendar generation"""
    
    def test_generate_ical_empty_bookings(self):
        """Test calendar generation with no bookings"""
        calendar_str = generate_ical([])
        
        assert "BEGIN:VCALENDAR" in calendar_str
        assert "END:VCALENDAR" in calendar_str
        assert "VERSION:2.0" in calendar_str
        assert "PRODID:Gibster" in calendar_str
        # Should not contain any events
        assert "BEGIN:VEVENT" not in calendar_str
    
    def test_generate_ical_single_booking(self, test_db):
        """Test calendar generation with single booking"""
        # Create a test booking
        booking = Booking(
            id="test-booking-1",
            user_id="test-user",
            name="R-490015",
            start_time=datetime(2024, 1, 15, 10, 0),
            end_time=datetime(2024, 1, 15, 12, 0),
            studio="Studio A",
            location="280 Broadway",
            status="Confirmed",
            price=50.00,
            record_url="https://gibney.my.site.com/s/rental-form?Id=test-booking-1"
        )
        
        calendar_str = generate_ical([booking])
        
        # Check calendar structure
        assert "BEGIN:VCALENDAR" in calendar_str
        assert "END:VCALENDAR" in calendar_str
        assert "VERSION:2.0" in calendar_str
        
        # Check event content
        assert "BEGIN:VEVENT" in calendar_str
        assert "END:VEVENT" in calendar_str
        assert "SUMMARY:R-490015 - Studio A" in calendar_str
        assert "LOCATION:Studio A, 280 Broadway" in calendar_str
        assert "DTSTART:20240115T100000Z" in calendar_str
        assert "DTEND:20240115T120000Z" in calendar_str
        assert "test-booking-1" in calendar_str
    
    def test_generate_ical_multiple_bookings(self, test_db):
        """Test calendar generation with multiple bookings"""
        bookings = [
            Booking(
                id="test-booking-1",
                user_id="test-user",
                name="R-490015",
                start_time=datetime(2024, 1, 15, 10, 0),
                end_time=datetime(2024, 1, 15, 12, 0),
                studio="Studio A",
                location="280 Broadway",
                status="Confirmed",
                price=50.00,
                record_url="https://gibney.my.site.com/s/rental-form?Id=test-booking-1"
            ),
            Booking(
                id="test-booking-2",
                user_id="test-user",
                name="R-490016",
                start_time=datetime(2024, 1, 16, 14, 0),
                end_time=datetime(2024, 1, 16, 16, 0),
                studio="Studio B",
                location="890 Broadway",
                status="Confirmed",
                price=75.00,
                record_url="https://gibney.my.site.com/s/rental-form?Id=test-booking-2"
            )
        ]
        
        calendar_str = generate_ical(bookings)
        
        # Should contain both events
        assert calendar_str.count("BEGIN:VEVENT") == 2
        assert calendar_str.count("END:VEVENT") == 2
        assert "R-490015 - Studio A" in calendar_str
        assert "R-490016 - Studio B" in calendar_str
        assert "280 Broadway" in calendar_str
        assert "890 Broadway" in calendar_str
    
    def test_generate_ical_special_characters(self, test_db):
        """Test calendar generation with special characters in booking data"""
        booking = Booking(
            id="test-booking-special",
            user_id="test-user",
            name="R-490015 (Special Event)",
            start_time=datetime(2024, 1, 15, 10, 0),
            end_time=datetime(2024, 1, 15, 12, 0),
            studio="Studio A & B",
            location="280 Broadway, NYC",
            status="Confirmed",
            price=50.00,
            record_url="https://gibney.my.site.com/s/rental-form?Id=test-booking-special"
        )
        
        calendar_str = generate_ical([booking])
        
        # Should handle special characters properly
        assert "BEGIN:VEVENT" in calendar_str
        assert "SUMMARY:" in calendar_str
        assert "LOCATION:" in calendar_str
    
    def test_generate_ical_cancelled_booking(self, test_db):
        """Test calendar generation with cancelled booking"""
        booking = Booking(
            id="test-booking-cancelled",
            user_id="test-user",
            name="R-490015",
            start_time=datetime(2024, 1, 15, 10, 0),
            end_time=datetime(2024, 1, 15, 12, 0),
            studio="Studio A",
            location="280 Broadway",
            status="Cancelled",
            price=50.00,
            record_url="https://gibney.my.site.com/s/rental-form?Id=test-booking-cancelled"
        )
        
        calendar_str = generate_ical([booking])
        
        # Should include cancelled status
        assert "BEGIN:VEVENT" in calendar_str
        assert "CANCELLED" in calendar_str.upper() or "STATUS:CANCELLED" in calendar_str 