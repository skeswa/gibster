import os
import re
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from ics import Calendar, Event
from playwright.sync_api import sync_playwright

LOGIN_URL = "https://gibney.my.site.com/s/login"
RENTALS_URL = "https://gibney.my.site.com/s/booking-item"


def main():
    """
    Logs into the Gibney website, scrapes the user's rentals,
    and generates an iCal file.
    """
    # Load environment variables from backend/.env
    backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend')
    env_path = os.path.join(backend_dir, '.env')
    load_dotenv(dotenv_path=env_path)
    gibney_email = os.getenv("GIBNEY_EMAIL")
    gibney_password = os.getenv("GIBNEY_PASSWORD")

    if not gibney_email or not gibney_password:
        print("GIBNEY_EMAIL and GIBNEY_PASSWORD must be set in .env file.")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False
        )  # Set headless=True for background execution
        page = browser.new_page()

        # Log in
        print("Logging in...")
        page.goto(LOGIN_URL)
        page.fill('input[type="text"]', gibney_email)
        page.fill('input[type="password"]', gibney_password)
        page.click('button[type="submit"]')

        # Navigate to rentals page
        print("Waiting for login redirect to home page...")
        page.wait_for_url(
            "https://gibney.my.site.com/s/"
        )  # Wait for redirect to home page

        print("Navigating to My Rentals...")
        # Try multiple selectors for the My Rentals link
        my_rentals_selectors = [
            'a:has-text("My Rentals")',
            'a[href*="booking-item"]',
            'a[href*="rental"]',
            'span:has-text("My Rentals")',
        ]

        rentals_link_clicked = False
        for selector in my_rentals_selectors:
            try:
                page.click(selector, timeout=5000)
                rentals_link_clicked = True
                print(f"Successfully clicked My Rentals with selector: {selector}")
                break
            except Exception as e:
                print(f"My Rentals selector {selector} failed: {e}")
                continue

        if not rentals_link_clicked:
            # If we can't find the My Rentals link, try to navigate directly to the rentals URL
            print("Could not find My Rentals link, navigating directly to rentals page")
            page.goto(RENTALS_URL)
        else:
            # Wait for navigation to rentals page
            print("Waiting for navigation to rentals page...")
            try:
                page.wait_for_url(
                    f"{RENTALS_URL}**", timeout=45000
                )  # Increased timeout to 45 seconds
            except Exception as nav_error:
                # Log current URL and page info for debugging
                current_url = page.url
                print(f"Failed to navigate to rentals page. Current URL: {current_url}")
                print(f"Navigation error: {nav_error}")

                # Check if we're already on a booking-related page
                if "booking" in current_url or "rental" in current_url:
                    print("Already on a booking-related page, proceeding...")
                else:
                    # Try direct navigation as fallback
                    print("Attempting direct navigation to rentals page as fallback...")
                    page.goto(RENTALS_URL, timeout=30000)

        # Use the provided HTML snapshot for scraping logic
        html_path = (
            Path(__file__).parent.parent
            / "resources/page_snapshots/rentals/Rentals.html"
        )
        content = html_path.read_text()

        print("Parsing rentals...")
        soup = BeautifulSoup(content, "lxml")
        cal = Calendar()

        rows = soup.select("table.forceRecordLayout tbody tr")

        for row in rows:
            cells = row.select("th, td")
            if not cells:
                continue

            try:
                rental_name = cells[1].select_one("a").get_text(strip=True)
                start_time_str = cells[2].get_text(strip=True)
                end_time_str = cells[3].get_text(strip=True)
                studio = cells[4].get_text(strip=True)
                price = cells[5].get_text(strip=True)
                status = cells[6].get_text(strip=True)
                location = cells[7].get_text(strip=True)
                record_url = cells[1].select_one("a")["href"]

                if status.lower() == "canceled":
                    continue

                # The date format is M/D/YYYY H:MM AM/PM
                start_dt = datetime.strptime(start_time_str, "%m/%d/%Y %I:%M %p")
                end_dt = datetime.strptime(end_time_str, "%m/%d/%Y %I:%M %p")

                event = Event()
                event.name = f"{studio} at {location}"
                event.begin = start_dt
                event.end = end_dt
                event.description = f"Rental: {rental_name}\nPrice: {price}\nStatus: {status}\nURL: {record_url}"
                event.location = location
                cal.events.add(event)

            except (AttributeError, IndexError, ValueError) as e:
                print(f"Skipping a row due to parsing error: {e}")
                continue

        # Save calendar to file
        output_path = Path("my_rentals.ics")
        with open(output_path, "w") as f:
            f.writelines(cal)

        print(f"Successfully created calendar file: {output_path}")

        browser.close()


if __name__ == "__main__":
    main()
