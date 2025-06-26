import asyncio
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, cast

from bs4 import BeautifulSoup, Tag
from playwright.async_api import Browser, Page, async_playwright
from sqlalchemy.orm import Session

from .auth import decrypt_credential
from .logging_config import get_logger
from .models import Booking, User

# Configure logging
logger = get_logger("scraper")

LOGIN_URL = "https://gibney.my.site.com/s/login"
RENTALS_URL = "https://gibney.my.site.com/s/booking-item"


def parse_booking_row(row_html: str) -> Dict[str, Any]:
    """Parse a booking row from HTML and extract booking data"""
    logger.debug("Parsing booking row from HTML")
    soup = BeautifulSoup(row_html, "html.parser")

    # Find cells - this is a mock implementation based on expected structure
    cells = soup.find_all(["td", "th"])

    if len(cells) < 7:
        logger.warning(
            f"Invalid row format - only {len(cells)} cells found, expected at least 7"
        )
        raise ValueError("Invalid row format - not enough cells")

    try:
        # Extract link and name from first cell
        link_cell = cast(Tag, cells[0])
        link = link_cell.find("a")
        if not link:
            logger.warning("No booking link found in first cell")
            raise ValueError("No booking link found")

        link = cast(Tag, link)
        name = link.get_text(strip=True)
        href = str(link.get("href", ""))

        # Extract booking ID from href
        id_match = re.search(r"Id=([a-zA-Z0-9]{15,18})", href)
        booking_id = id_match.group(1) if id_match else f"unknown_{name}"

        # Parse datetime strings (assuming format like "Jan 15, 2024 10:00 AM")
        start_time_str = cast(Tag, cells[1]).get_text(strip=True)
        end_time_str = cast(Tag, cells[2]).get_text(strip=True)

        try:
            start_time = datetime.strptime(start_time_str, "%b %d, %Y %I:%M %p")
            end_time = datetime.strptime(end_time_str, "%b %d, %Y %I:%M %p")
        except ValueError as e:
            logger.warning(
                f"Failed to parse dates '{start_time_str}' and '{end_time_str}': {e}"
            )
            # If parsing fails, use a default format
            start_time = datetime.now()
            end_time = datetime.now()

        studio = cast(Tag, cells[3]).get_text(strip=True)
        location = cast(Tag, cells[4]).get_text(strip=True)
        status = cast(Tag, cells[5]).get_text(strip=True)

        # Parse price
        price_str = (
            cast(Tag, cells[6]).get_text(strip=True) if len(cells) > 6 else "$0.00"
        )
        price = 0.0
        if price_str.startswith("$"):
            try:
                price = float(price_str[1:].replace(",", ""))
            except ValueError:
                logger.warning(f"Failed to parse price: {price_str}")
                price = 0.0

        # Build full URL
        record_url = (
            f"https://gibney.my.site.com{href}" if href.startswith("/") else href
        )

        booking_data = {
            "id": booking_id,
            "name": name,
            "start_time": start_time.strftime("%Y-%m-%dT%H:%M:%S"),
            "end_time": end_time.strftime("%Y-%m-%dT%H:%M:%S"),
            "studio": studio,
            "location": location,
            "status": status,
            "price": price,
            "record_url": record_url,
        }

        logger.debug(f"Successfully parsed booking: {name} at {studio}")
        return booking_data

    except Exception as e:
        logger.error(f"Failed to parse booking row: {e}")
        raise


def parse_price(price_str: str) -> float:
    """Parse price string and return float value"""
    logger.debug(f"Parsing price string: {price_str}")

    if not price_str or price_str.lower() == "free":
        return 0.0

    if price_str.startswith("$"):
        try:
            return float(price_str[1:].replace(",", ""))
        except ValueError:
            logger.warning(f"Failed to parse price: {price_str}")
            return 0.0

    try:
        return float(price_str)
    except ValueError:
        logger.warning(f"Failed to parse price: {price_str}")
        return 0.0


class GibneyScrapingError(Exception):
    """Raised when scraping fails"""

    pass


class GibneyScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        logger.info(f"Initializing Gibney scraper (headless: {headless})")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # For sync context manager, we can't await, so we'll just set browser to None
        # The actual browser cleanup will happen when the object is garbage collected
        if self.browser:
            logger.debug("Sync context manager exit - browser will be cleaned up")
            self.browser = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            logger.debug("Closing browser")
            await self.browser.close()

    async def login(self, email: str, password: str) -> None:
        """Log into Gibney website"""
        logger.info(f"Attempting to login to Gibney for user: {email}")

        try:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(headless=self.headless)
            self.page = await self.browser.new_page()

            logger.info("Navigating to login page...")
            await self.page.goto(LOGIN_URL)

            # Fill login form
            logger.debug("Filling login form")
            # The Gibney login page uses type-based selectors, not name attributes
            await self.page.fill('input[type="text"]', email)
            await self.page.fill('input[type="password"]', password)

            # Submit form - try multiple selectors since the button might not have type="submit"
            logger.info("Submitting login form...")

            # Try different button selectors in order of preference
            button_selectors = [
                'button[type="submit"]',
                "button.loginButton",
                'button[class*="loginButton"]',
                'button[aria-label*="Log in"]',
                'button:has-text("Log in")',
                'button[class*="uiButton"]',
            ]

            button_clicked = False
            for selector in button_selectors:
                try:
                    logger.debug(f"Trying button selector: {selector}")
                    await self.page.click(selector, timeout=5000)
                    button_clicked = True
                    logger.debug(
                        f"Successfully clicked button with selector: {selector}"
                    )
                    break
                except Exception as e:
                    logger.debug(f"Button selector {selector} failed: {e}")
                    continue

            if not button_clicked:
                raise Exception(
                    "Could not find or click login button with any selector"
                )

            # Wait for redirect to home page after login
            logger.debug("Waiting for login redirect to home page...")
            await self.page.wait_for_url("https://gibney.my.site.com/s/", timeout=30000)
            logger.debug("Successfully redirected to home page")

            # Now navigate to My Rentals by clicking the link
            logger.debug("Looking for 'My Rentals' link...")

            # Try multiple selectors for the My Rentals link
            my_rentals_selectors = [
                'a:has-text("My Rentals")',
                'a[href*="booking-item"]',
                'a[href*="rental"]',
                'span:has-text("My Rentals")',
                'li:has-text("My Rentals") a',
                'community_navigation-global-navigation-item:has-text("My Rentals") a',
            ]

            rentals_link_clicked = False
            for selector in my_rentals_selectors:
                try:
                    logger.debug(f"Trying My Rentals selector: {selector}")
                    await self.page.click(selector, timeout=5000)
                    rentals_link_clicked = True
                    logger.debug(
                        f"Successfully clicked My Rentals with selector: {selector}"
                    )
                    break
                except Exception as e:
                    logger.debug(f"My Rentals selector {selector} failed: {e}")
                    continue

            if not rentals_link_clicked:
                # If we can't find the My Rentals link, try to navigate directly to the rentals URL
                logger.warning(
                    "Could not find My Rentals link, navigating directly to rentals page"
                )
                await self.page.goto(RENTALS_URL)
            else:
                # Wait for navigation to rentals page
                logger.debug("Waiting for navigation to rentals page...")
                try:
                    await self.page.wait_for_url(
                        f"{RENTALS_URL}**", timeout=45000
                    )  # Increased timeout to 45 seconds
                except Exception as nav_error:
                    # Log current URL and page info for debugging
                    current_url = self.page.url
                    logger.warning(
                        f"Failed to navigate to rentals page. Current URL: {current_url}"
                    )
                    logger.debug(f"Navigation error: {nav_error}")

                    # Check if we're already on a booking-related page
                    if "booking" in current_url or "rental" in current_url:
                        logger.info("Already on a booking-related page, proceeding...")
                    else:
                        # Try direct navigation as fallback
                        logger.warning(
                            "Attempting direct navigation to rentals page as fallback..."
                        )
                        await self.page.goto(RENTALS_URL, timeout=30000)

            logger.info(f"Login successful for user: {email}")

        except Exception as e:
            logger.error(f"Login failed for user {email}: {e}")
            raise GibneyScrapingError(f"Failed to login: {e}")

    async def scrape_rentals(self) -> List[Dict[str, Any]]:
        """Scrape rental data from the rentals page"""
        if not self.page:
            logger.error("Attempted to scrape rentals without logging in first")
            raise GibneyScrapingError("Must login first")

        try:
            logger.info("Starting rental data scraping...")

            # Navigate to rentals page if not already there
            if RENTALS_URL not in self.page.url:
                logger.debug("Navigating to rentals page")
                await self.page.goto(RENTALS_URL)

            # Wait for page to load
            logger.debug("Waiting for rental table to load")
            await self.page.wait_for_selector("table.forceRecordLayout", timeout=30000)

            # Get page content
            content = await self.page.content()
            soup = BeautifulSoup(content, "lxml")

            rentals = []
            rows = soup.select("table.forceRecordLayout tbody tr")

            logger.info(f"Found {len(rows)} rental rows to process")

            for i, row in enumerate(rows):
                cells = row.select("th, td")
                if not cells or len(cells) < 8:
                    logger.debug(
                        f"Skipping row {i+1}: insufficient cells ({len(cells)})"
                    )
                    continue

                try:
                    # Extract data from each cell
                    rental_link = cells[1].select_one("a")
                    if not rental_link:
                        logger.debug(f"Skipping row {i+1}: no rental link found")
                        continue

                    rental_name = rental_link.get_text(strip=True)
                    start_time_str = cells[2].get_text(strip=True)
                    end_time_str = cells[3].get_text(strip=True)
                    studio = cells[4].get_text(strip=True)
                    price_str = cells[5].get_text(strip=True)
                    status = cells[6].get_text(strip=True)
                    location = cells[7].get_text(strip=True)

                    # Extract record ID from href
                    href = str(rental_link.get("href", ""))
                    record_id_match = re.search(r"/([a-zA-Z0-9]{15,18})/", href)
                    record_id = (
                        record_id_match.group(1)
                        if record_id_match
                        else f"unknown_{rental_name}"
                    )

                    # Parse dates
                    try:
                        start_dt = datetime.strptime(
                            start_time_str, "%b %d, %Y %I:%M %p"
                        )
                        end_dt = datetime.strptime(end_time_str, "%b %d, %Y %I:%M %p")
                    except ValueError as e:
                        logger.warning(f"Failed to parse dates for {rental_name}: {e}")
                        # Use current time as fallback
                        start_dt = datetime.now()
                        end_dt = datetime.now()

                    # Parse price
                    price = parse_price(price_str)

                    # Build rental data
                    rental = {
                        "id": record_id,
                        "name": rental_name,
                        "start_time": start_dt,
                        "end_time": end_dt,
                        "studio": studio,
                        "location": location,
                        "status": status,
                        "price": price,
                        "record_url": (
                            f"https://gibney.my.site.com{href}"
                            if href.startswith("/")
                            else href
                        ),
                    }

                    rentals.append(rental)
                    logger.debug(f"Scraped rental: {rental_name}")

                except Exception as e:
                    logger.warning(f"Skipping row {i+1} due to parsing error: {e}")
                    continue

            logger.info(f"Successfully scraped {len(rentals)} rentals")
            return rentals

        except Exception as e:
            logger.error(f"Failed to scrape rentals: {e}")
            raise GibneyScrapingError(f"Failed to scrape rentals: {e}")


async def scrape_user_bookings(db: Session, user: User) -> List[Booking]:
    """Scrape bookings for a specific user and update the database"""
    logger.info(f"Starting booking scrape for user: {user.email}")

    try:
        # Get encrypted credentials
        if user.gibney_email is None or user.gibney_password is None:
            logger.error(f"Missing Gibney credentials for user: {user.email}")
            raise ValueError("Gibney credentials not set")

        # Decrypt credentials
        logger.debug("Decrypting user credentials")
        gibney_email = decrypt_credential(str(user.gibney_email))
        gibney_password = decrypt_credential(str(user.gibney_password))

        # Scrape data
        async with GibneyScraper(headless=True) as scraper:
            await scraper.login(gibney_email, gibney_password)
            rental_data = await scraper.scrape_rentals()

        logger.info(
            f"Scraped {len(rental_data)} rentals from Gibney for user: {user.email}"
        )

        # Convert to Booking objects and update database
        updated_bookings = []

        # Remove old bookings that are no longer in the scraped data
        existing_booking_ids = {booking["id"] for booking in rental_data}
        old_bookings = (
            db.query(Booking)
            .filter(Booking.user_id == user.id)
            .filter(~Booking.id.in_(existing_booking_ids))
            .all()
        )

        for old_booking in old_bookings:
            logger.info(f"Removing old booking: {old_booking.name}")
            db.delete(old_booking)

        # Update or create bookings
        for booking_data in rental_data:
            try:
                # Check if booking already exists
                existing_booking = (
                    db.query(Booking)
                    .filter(Booking.id == booking_data["id"])
                    .filter(Booking.user_id == user.id)
                    .first()
                )

                if existing_booking:
                    # Update existing booking
                    for key, value in booking_data.items():
                        if key != "id":  # Don't update the ID
                            setattr(existing_booking, key, value)
                    setattr(existing_booking, "last_seen", datetime.utcnow())
                    updated_bookings.append(existing_booking)
                    logger.debug(f"Updated existing booking: {booking_data['name']}")
                else:
                    # Create new booking
                    new_booking = Booking(
                        id=booking_data["id"],
                        user_id=user.id,
                        name=booking_data["name"],
                        start_time=booking_data["start_time"],
                        end_time=booking_data["end_time"],
                        studio=booking_data["studio"],
                        location=booking_data["location"],
                        status=booking_data["status"],
                        price=booking_data["price"],
                        record_url=booking_data["record_url"],
                        last_seen=datetime.utcnow(),
                    )
                    db.add(new_booking)
                    updated_bookings.append(new_booking)
                    logger.debug(f"Created new booking: {booking_data['name']}")

            except Exception as e:
                logger.error(
                    f"Failed to process booking {booking_data.get('name', 'unknown')}: {e}"
                )
                continue

        # Commit changes
        db.commit()

        logger.info(f"Updated {len(updated_bookings)} bookings for user {user.email}")
        return updated_bookings

    except Exception as e:
        logger.error(f"Failed to scrape bookings for user {user.email}: {e}")
        db.rollback()
        raise


def scrape_user_bookings_sync(db: Session, user: User) -> List[Booking]:
    """Synchronous wrapper for scrape_user_bookings - runs async version in new event loop"""
    logger.info(f"Starting synchronous booking scrape for user: {user.email}")

    try:
        # Run the async version in a new event loop
        return asyncio.run(scrape_user_bookings(db, user))
    except Exception as e:
        logger.error(
            f"Failed to scrape bookings synchronously for user {user.email}: {e}"
        )
        raise
