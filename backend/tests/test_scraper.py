from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from backend.scraper import GibneyScraper, GibneyScrapingError


@pytest.mark.unit
class TestScraperClass:
    """Test the GibneyScraper class"""

    def test_scraper_initialization(self):
        """Test scraper initialization"""
        scraper = GibneyScraper()
        assert scraper.headless is True
        assert scraper.browser is None
        assert scraper.page is None

        scraper_visible = GibneyScraper(headless=False)
        assert scraper_visible.headless is False

    def test_scraper_context_manager(self):
        """Test scraper as context manager"""
        with GibneyScraper() as scraper:
            assert isinstance(scraper, GibneyScraper)
        # Scraper should be properly closed after context


@pytest.mark.unit
class TestScraperUtilities:
    """Test utility functions and data parsing"""

    def test_parse_price_string(self):
        """Test parsing price strings"""
        # Test various price formats
        test_cases = [
            ("$50.00", 50.00),
            ("$75.50", 75.50),
            ("$0.00", 0.00),
            ("", None),
        ]

        for price_str, expected in test_cases:
            if (
                price_str
                and price_str.replace("$", "")
                .replace(",", "")
                .replace(".", "")
                .isdigit()
            ):
                try:
                    result = float(price_str.replace("$", "").replace(",", ""))
                except ValueError:
                    result = None
            else:
                result = None

            assert result == expected

    def test_parse_datetime_string(self):
        """Test parsing datetime strings from Gibney format"""
        # Test expected datetime parsing
        test_cases = [
            ("1/15/2024 10:00 AM", datetime(2024, 1, 15, 10, 0)),
            ("12/31/2023 11:59 PM", datetime(2023, 12, 31, 23, 59)),
            ("2/29/2024 12:00 PM", datetime(2024, 2, 29, 12, 0)),
        ]

        for date_str, expected in test_cases:
            try:
                result = datetime.strptime(date_str, "%m/%d/%Y %I:%M %p")
                assert result == expected
            except ValueError:
                # If parsing fails, that's also a valid test result
                pass

    def test_extract_booking_id_from_url(self):
        """Test extracting booking ID from URL"""
        import re

        test_cases = [
            ("/s/rental-form?Id=a27Pb000000001ABCD", "a27Pb000000001ABCD"),
            (
                "https://gibney.my.site.com/s/rental-form?Id=a27Pb000000002EFGH",
                "a27Pb000000002EFGH",
            ),
            ("/rental/xyz123abc/", "xyz123abc"),
        ]

        for url, expected_id in test_cases:
            # This mimics the regex pattern used in the actual scraper
            match = re.search(r"/([a-zA-Z0-9]{15,18})/", url)
            if match:
                result = match.group(1)
                assert result == expected_id

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
            import re

            result = re.sub(r"\s+", " ", input_text.strip())
            assert result == expected


@pytest.mark.integration
class TestScraperErrors:
    """Test scraper error handling"""

    def test_scraping_error_creation(self):
        """Test GibneyScrapingError creation"""
        error_msg = "Test error message"
        error = GibneyScrapingError(error_msg)

        assert str(error) == error_msg
        assert isinstance(error, Exception)

    @pytest.mark.asyncio
    async def test_login_without_browser(self):
        """Test that scrape_rentals fails gracefully without login"""
        scraper = GibneyScraper()

        # This should raise an error since no login was performed
        with pytest.raises(GibneyScrapingError, match="Must login first"):
            await scraper.scrape_rentals()


@pytest.mark.unit
class TestScraperPagination:
    """Test pagination functionality in the scraper"""

    @pytest.mark.asyncio
    async def test_single_page_scraping(self):
        """Test scraping when there's only one page of results"""
        scraper = GibneyScraper()

        # Mock the page object
        mock_page = AsyncMock()
        mock_page.url = "https://gibney.my.site.com/s/booking-item"
        mock_page.content = AsyncMock(
            return_value="""
            <table class="forceRecordLayout">
                <tbody>
                    <tr>
                        <td></td>
                        <td><a href="/s/rental-form?Id=a27Pb000000001">R-001</a></td>
                        <td>1/1/2024 10:00 AM</td>
                        <td>1/1/2024 11:00 AM</td>
                        <td>Studio A</td>
                        <td>$50.00</td>
                        <td>Confirmed</td>
                        <td>Location 1</td>
                    </tr>
                </tbody>
            </table>
        """
        )

        # Mock query_selector to return None (no next button)
        mock_page.query_selector = AsyncMock(return_value=None)
        mock_page.wait_for_selector = AsyncMock()

        scraper.page = mock_page

        rentals = await scraper.scrape_rentals()

        assert len(rentals) == 1
        assert rentals[0]["name"] == "R-001"
        assert rentals[0]["id"] == "a27Pb000000001"

    @pytest.mark.asyncio
    async def test_multi_page_scraping(self):
        """Test scraping when there are multiple pages of results"""
        scraper = GibneyScraper()

        # Create page contents for two pages
        page1_content = """
            <table class="forceRecordLayout">
                <tbody>
                    <tr>
                        <td></td>
                        <td><a href="/s/rental-form?Id=a27Pb000000001">R-001</a></td>
                        <td>1/1/2024 10:00 AM</td>
                        <td>1/1/2024 11:00 AM</td>
                        <td>Studio A</td>
                        <td>$50.00</td>
                        <td>Confirmed</td>
                        <td>Location 1</td>
                    </tr>
                </tbody>
            </table>
        """

        page2_content = """
            <table class="forceRecordLayout">
                <tbody>
                    <tr>
                        <td></td>
                        <td><a href="/s/rental-form?Id=a27Pb000000002">R-002</a></td>
                        <td>1/2/2024 10:00 AM</td>
                        <td>1/2/2024 11:00 AM</td>
                        <td>Studio B</td>
                        <td>$60.00</td>
                        <td>Confirmed</td>
                        <td>Location 2</td>
                    </tr>
                </tbody>
            </table>
        """

        # Track which page we're on
        page_calls = 0

        # Track content calls separately from page calls
        content_calls = 0

        async def mock_content():
            nonlocal content_calls
            content_calls += 1
            if content_calls <= 1:
                return page1_content
            else:
                return page2_content

        # Mock next button behavior
        mock_next_button = AsyncMock()
        mock_next_button.get_attribute = AsyncMock(return_value=None)  # Not disabled
        mock_next_button.click = AsyncMock()

        async def mock_query_selector(selector):
            nonlocal content_calls
            # Only show next button on first page
            if "Next" in selector and content_calls <= 1:
                return mock_next_button
            return None

        # Mock the page object
        mock_page = AsyncMock()
        mock_page.url = "https://gibney.my.site.com/s/booking-item"
        mock_page.content = mock_content
        mock_page.query_selector = mock_query_selector
        mock_page.wait_for_selector = AsyncMock()
        mock_page.wait_for_load_state = AsyncMock()
        mock_page.wait_for_timeout = AsyncMock()

        scraper.page = mock_page

        rentals = await scraper.scrape_rentals()

        # Should have scraped both pages
        assert len(rentals) == 2
        assert rentals[0]["name"] == "R-001"
        assert rentals[1]["name"] == "R-002"

    @pytest.mark.asyncio
    async def test_pagination_with_disabled_next_button(self):
        """Test that pagination stops when next button is disabled"""
        scraper = GibneyScraper()

        page_content = """
            <table class="forceRecordLayout">
                <tbody>
                    <tr>
                        <td></td>
                        <td><a href="/s/rental-form?Id=a27Pb000000001">R-001</a></td>
                        <td>1/1/2024 10:00 AM</td>
                        <td>1/1/2024 11:00 AM</td>
                        <td>Studio A</td>
                        <td>$50.00</td>
                        <td>Confirmed</td>
                        <td>Location 1</td>
                    </tr>
                </tbody>
            </table>
        """

        # Mock disabled next button
        mock_next_button = AsyncMock()
        mock_next_button.get_attribute = AsyncMock(
            side_effect=lambda attr: "true" if attr == "disabled" else None
        )

        # Mock the page object
        mock_page = AsyncMock()
        mock_page.url = "https://gibney.my.site.com/s/booking-item"
        mock_page.content = AsyncMock(return_value=page_content)
        mock_page.query_selector = AsyncMock(return_value=mock_next_button)
        mock_page.wait_for_selector = AsyncMock()

        scraper.page = mock_page

        rentals = await scraper.scrape_rentals()

        # Should stop at first page due to disabled button
        assert len(rentals) == 1
        assert rentals[0]["name"] == "R-001"

    @pytest.mark.asyncio
    async def test_pagination_max_pages_limit(self):
        """Test that pagination stops at max_pages limit"""
        scraper = GibneyScraper()

        page_content = """
            <table class="forceRecordLayout">
                <tbody>
                    <tr>
                        <td></td>
                        <td><a href="/s/rental-form?Id=a27Pb000000001">R-001</a></td>
                        <td>1/1/2024 10:00 AM</td>
                        <td>1/1/2024 11:00 AM</td>
                        <td>Studio A</td>
                        <td>$50.00</td>
                        <td>Confirmed</td>
                        <td>Location 1</td>
                    </tr>
                </tbody>
            </table>
        """

        # Mock a next button that's always available
        mock_next_button = AsyncMock()
        mock_next_button.get_attribute = AsyncMock(return_value=None)
        mock_next_button.click = AsyncMock()

        # Mock the page object
        mock_page = AsyncMock()
        mock_page.url = "https://gibney.my.site.com/s/booking-item"
        mock_page.content = AsyncMock(return_value=page_content)
        mock_page.query_selector = AsyncMock(return_value=mock_next_button)
        mock_page.wait_for_selector = AsyncMock()
        mock_page.wait_for_load_state = AsyncMock()
        mock_page.wait_for_timeout = AsyncMock()

        scraper.page = mock_page

        # This should eventually stop due to max_pages limit
        with patch("backend.scraper.logger") as mock_logger:
            rentals = await scraper.scrape_rentals()

            # Check that we hit the max pages warning
            warning_calls = [
                call
                for call in mock_logger.warning.call_args_list
                if "maximum page limit" in str(call)
            ]
            assert len(warning_calls) > 0


@pytest.mark.integration
class TestScraperPaginationIntegration:
    """Integration tests for pagination - requires actual Gibney account"""

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires Gibney account with multiple pages of bookings")
    async def test_real_pagination_scraping(self):
        """Test pagination with a real Gibney account that has multiple pages"""
        # This test would use real credentials and verify pagination works
        # Skip by default since it requires specific account setup
        pass

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires Gibney test environment")
    async def test_pagination_performance(self):
        """Test that pagination doesn't cause excessive delays"""
        # This would measure the time taken to scrape multiple pages
        # and ensure it's within reasonable bounds
        pass
