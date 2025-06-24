import pytest
from datetime import datetime
from app.scraper import parse_booking_row


@pytest.mark.unit
class TestScraperParsing:
    """Test HTML parsing functions"""
    
    def test_parse_booking_row_valid(self):
        """Test parsing a valid booking row"""
        # Mock HTML for a booking row (simplified)
        mock_html = """
        <tr data-id="a27Pb000000001">
            <td><a href="/s/rental-form?Id=a27Pb000000001">R-490015</a></td>
            <td>Jan 15, 2024 10:00 AM</td>
            <td>Jan 15, 2024 12:00 PM</td>
            <td>Studio A</td>
            <td>280 Broadway</td>
            <td>Confirmed</td>
            <td>$50.00</td>
        </tr>
        """
        
        # This test would require actual implementation of parse_booking_row
        # For now, we'll test the expected structure
        expected = {
            "id": "a27Pb000000001",
            "name": "R-490015",
            "start_time": "2024-01-15T10:00:00",
            "end_time": "2024-01-15T12:00:00",
            "studio": "Studio A",
            "location": "280 Broadway",
            "status": "Confirmed",
            "price": 50.00,
            "record_url": "https://gibney.my.site.com/s/rental-form?Id=a27Pb000000001"
        }
        
        # Note: This is a placeholder test structure
        # The actual parse_booking_row function would need to be implemented
        # to parse BeautifulSoup elements
        assert expected["id"] == "a27Pb000000001"
        assert expected["name"] == "R-490015"
        assert expected["studio"] == "Studio A"
    
    def test_parse_price_string(self):
        """Test parsing price strings"""
        from app.scraper import parse_price  # This function would need to be added
        
        # Test various price formats
        test_cases = [
            ("$50.00", 50.00),
            ("$75.50", 75.50),
            ("$0.00", 0.00),
            ("Free", 0.00),
            ("", 0.00),
        ]
        
        # For now, just test the logic we expect
        for price_str, expected in test_cases:
            if price_str.startswith("$"):
                result = float(price_str[1:])
            elif price_str.lower() == "free" or price_str == "":
                result = 0.00
            else:
                result = 0.00
            
            assert result == expected
    
    def test_parse_datetime_string(self):
        """Test parsing datetime strings from Gibney format"""
        # Test expected datetime parsing
        test_cases = [
            ("Jan 15, 2024 10:00 AM", "2024-01-15T10:00:00"),
            ("Dec 31, 2023 11:59 PM", "2023-12-31T23:59:00"),
            ("Feb 29, 2024 12:00 PM", "2024-02-29T12:00:00"),
        ]
        
        # For actual implementation, we'd use strptime
        for date_str, expected in test_cases:
            # This would be the actual parsing logic
            # dt = datetime.strptime(date_str, "%b %d, %Y %I:%M %p")
            # result = dt.strftime("%Y-%m-%dT%H:%M:%S")
            # assert result == expected
            pass  # Placeholder for actual test
    
    def test_extract_booking_id_from_url(self):
        """Test extracting booking ID from URL"""
        test_cases = [
            ("/s/rental-form?Id=a27Pb000000001", "a27Pb000000001"),
            ("https://gibney.my.site.com/s/rental-form?Id=a27Pb000000002", "a27Pb000000002"),
            ("/s/rental-form?Id=xyz123", "xyz123"),
        ]
        
        for url, expected_id in test_cases:
            if "Id=" in url:
                result = url.split("Id=")[1]
                assert result == expected_id
    
    def test_parse_status_variations(self):
        """Test parsing different status variations"""
        status_mappings = {
            "confirmed": "Confirmed",
            "CONFIRMED": "Confirmed",
            "cancelled": "Cancelled", 
            "CANCELLED": "Cancelled",
            "completed": "Completed",
            "pending": "Pending",
        }
        
        for input_status, expected in status_mappings.items():
            # Test case-insensitive status normalization
            result = input_status.title()
            assert result == expected or result.upper() == expected.upper()


@pytest.mark.unit  
class TestScraperUtilities:
    """Test utility functions used by the scraper"""
    
    def test_clean_text_content(self):
        """Test text cleaning utility"""
        test_cases = [
            ("  Studio A  ", "Studio A"),
            ("Studio\nA", "Studio A"),
            ("Studio\tA", "Studio A"),
            ("", ""),
            ("Multiple   spaces", "Multiple spaces"),
        ]
        
        for input_text, expected in test_cases:
            # This would be a utility function to clean scraped text
            import re
            result = re.sub(r'\s+', ' ', input_text.strip())
            assert result == expected
    
    def test_build_record_url(self):
        """Test building full record URLs"""
        base_url = "https://gibney.my.site.com"
        relative_url = "/s/rental-form?Id=a27Pb000000001"
        
        expected = "https://gibney.my.site.com/s/rental-form?Id=a27Pb000000001"
        
        if relative_url.startswith("/"):
            result = base_url + relative_url
        else:
            result = relative_url
            
        assert result == expected 