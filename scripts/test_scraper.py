#!/usr/bin/env python3
"""
Test script for the Gibster scraper
This can be used to test scraping functionality with your Gibney credentials
"""

import os
import sys

from dotenv import load_dotenv

# Add the app directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "app"))

from app.calendar_generator import generate_ical_calendar
from app.scraper import GibneyScraper


def test_scraper():
    """Test the scraper functionality"""
    load_dotenv()

    gibney_email = os.getenv("GIBNEY_EMAIL")
    gibney_password = os.getenv("GIBNEY_PASSWORD")

    if not gibney_email or not gibney_password:
        print("Please set GIBNEY_EMAIL and GIBNEY_PASSWORD in your .env file")
        return

    try:
        print("Testing Gibney scraper...")

        with GibneyScraper(headless=False) as scraper:  # Set to False to see browser
            print("Logging in...")
            scraper.login(gibney_email, gibney_password)

            print("Scraping rentals...")
            rentals = scraper.scrape_rentals()

            print(f"Found {len(rentals)} rentals:")
            for rental in rentals:
                print(
                    f"  - {rental['name']}: {rental['studio']} at {rental['location']}"
                )
                print(f"    {rental['start_time']} - {rental['end_time']}")
                print(
                    f"    Status: {rental['status']}, Price: ${rental['price'] or 'N/A'}"
                )
                print()

        # Test calendar generation
        print("Testing calendar generation...")

        # Create a mock user object for calendar generation
        class MockUser:
            def __init__(self, email):
                self.email = email

        # Create mock booking objects
        class MockBooking:
            def __init__(self, rental_data):
                self.id = rental_data["id"]
                self.name = rental_data["name"]
                self.start_time = rental_data["start_time"]
                self.end_time = rental_data["end_time"]
                self.studio = rental_data["studio"]
                self.location = rental_data["location"]
                self.status = rental_data["status"]
                self.price = rental_data["price"]
                self.record_url = rental_data["record_url"]

        mock_user = MockUser(gibney_email)
        mock_bookings = [MockBooking(rental) for rental in rentals]

        calendar_content = generate_ical_calendar(mock_user, mock_bookings)

        # Save calendar to file
        output_file = "test_calendar.ics"
        with open(output_file, "w") as f:
            f.write(calendar_content)

        print(f"Calendar saved to {output_file}")
        print("Test completed successfully!")

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_scraper()
