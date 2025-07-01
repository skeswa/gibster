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
        """Scrape rental data from the rentals page, handling pagination
        
        This method will:
        1. Navigate to the rentals page if not already there
        2. Scrape all bookings from the current page
        3. Look for pagination controls (Next button)
        4. Continue to next pages until no more pages exist
        5. Return all bookings from all pages
        
        Returns:
            List of rental dictionaries containing booking information
            
        Raises:
            GibneyScrapingError: If scraping fails or login wasn't performed
        """
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

            all_rentals = []
            page_number = 1
            max_pages = 100  # Safety limit to prevent infinite loops
            
            while page_number <= max_pages:
                logger.info(f"Scraping page {page_number}...")
                
                # Get page content
                content = await self.page.content()
                soup = BeautifulSoup(content, "lxml")

                # Debug: Check what tables are available (only log on first page)
                if page_number == 1:
                    all_tables = soup.select("table")
                    logger.debug(f"Found {len(all_tables)} tables on the page")
                    for j, table in enumerate(all_tables):
                        table_classes = table.get("class") or []
                        logger.debug(f"  Table {j}: classes={table_classes}")

                rows = soup.select("table.forceRecordLayout tbody tr")

                logger.info(f"Found {len(rows)} rental rows to process on page {page_number}")

                # If no rows found, try alternative selectors
                if len(rows) == 0:
                    logger.warning(
                        "No rows found with primary selector, trying alternatives..."
                    )
                    alternative_selectors = [
                        "table tbody tr",
                        ".forceRecordLayout tbody tr",
                        "[data-aura-class*='uiVirtualDataTable'] tbody tr",
                        "tbody tr",
                    ]

                    for alt_selector in alternative_selectors:
                        alt_rows = soup.select(alt_selector)
                        logger.debug(
                            f"Alternative selector '{alt_selector}' found {len(alt_rows)} rows"
                        )
                        if len(alt_rows) > 0:
                            rows = alt_rows
                            logger.info(
                                f"Using alternative selector '{alt_selector}' with {len(rows)} rows"
                            )
                            break

                # Process rows on current page
                page_rentals = []
                for i, row in enumerate(rows):
                    cells = row.select("th, td")
                    if not cells or len(cells) < 8:
                        logger.debug(
                            f"Skipping row {i+1}: insufficient cells ({len(cells)})"
                        )
                        continue

                    try:
                        # Debug: Log all cell contents for troubleshooting
                        logger.debug(f"Row {i+1} has {len(cells)} cells:")
                        for j, cell in enumerate(cells):
                            cell_text = cell.get_text(strip=True)
                            logger.debug(f"  Cell {j}: '{cell_text}'")

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

                        logger.debug(f"Extracted data for {rental_name}:")
                        logger.debug(f"  Start time: '{start_time_str}'")
                        logger.debug(f"  End time: '{end_time_str}'")
                        logger.debug(f"  Studio: '{studio}'")
                        logger.debug(f"  Price: '{price_str}'")
                        logger.debug(f"  Status: '{status}'")
                        logger.debug(f"  Location: '{location}'")

                        # Extract record ID from href
                        href = str(rental_link.get("href", ""))
                        # Try both URL patterns: query parameter and path segment
                        # Also handle IDs that may be shorter than 15 characters
                        record_id_match = re.search(r"Id=([a-zA-Z0-9]+)", href) or re.search(r"/([a-zA-Z0-9]{15,18})/", href)
                        record_id = (
                            record_id_match.group(1)
                            if record_id_match
                            else f"unknown_{rental_name}"
                        )

                        # Parse dates with multiple format support
                        try:
                            logger.debug(
                                f"Parsing start_time: '{start_time_str}', end_time: '{end_time_str}'"
                            )

                            # Try multiple date formats that Gibney might use
                            date_formats = [
                                "%m/%d/%Y %I:%M %p",  # 6/9/2025 7:00 PM
                                "%b %d, %Y %I:%M %p",  # Jun 26, 2025 5:01 PM
                                "%m/%d/%Y %H:%M",  # 6/9/2025 19:00
                                "%Y-%m-%d %H:%M:%S",  # 2025-06-09 19:00:00
                                "%Y-%m-%dT%H:%M:%S",  # 2025-06-09T19:00:00
                            ]

                            start_dt = None
                            end_dt = None

                            # Try parsing start time with different formats
                            for date_format in date_formats:
                                try:
                                    start_dt = datetime.strptime(
                                        start_time_str, date_format
                                    )
                                    end_dt = datetime.strptime(end_time_str, date_format)
                                    logger.debug(
                                        f"Successfully parsed dates using format: {date_format}"
                                    )
                                    break
                                except ValueError:
                                    continue

                            # If all parsing attempts failed
                            if start_dt is None or end_dt is None:
                                logger.warning(
                                    f"Failed to parse dates for {rental_name}: start='{start_time_str}', end='{end_time_str}'"
                                )
                                logger.warning(
                                    "All date format attempts failed, using fallback"
                                )
                                # Use current time as fallback
                                start_dt = datetime.now()
                                end_dt = datetime.now()
                            else:
                                logger.debug(
                                    f"Parsed dates successfully: {start_dt} to {end_dt}"
                                )

                        except Exception as e:
                            logger.warning(
                                f"Exception during date parsing for {rental_name}: {e}"
                            )
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

                        page_rentals.append(rental)
                        logger.debug(f"Scraped rental: {rental_name}")

                    except Exception as e:
                        logger.warning(f"Skipping row {i+1} due to parsing error: {e}")
                        continue

                # Add this page's rentals to the total
                all_rentals.extend(page_rentals)
                logger.info(f"Scraped {len(page_rentals)} rentals from page {page_number}")
                
                # Check for pagination controls
                logger.debug("Looking for pagination controls...")
                
                # Common pagination selectors to try
                pagination_selectors = [
                    'button:has-text("Next")',
                    'a:has-text("Next")',
                    'button[aria-label*="Next"]',
                    'a[aria-label*="Next"]',
                    '.slds-button:has-text("Next")',
                    'lightning-button:has-text("Next")',
                    'button.nextButton',
                    'a.next-page',
                    '[data-aura-class*="uiPager"] button:has-text("Next")',
                    '.uiPager button:has-text("Next")',
                    'button[title="Next Page"]',
                    'a[title="Next Page"]',
                ]
                
                next_button_found = False
                for selector in pagination_selectors:
                    try:
                        # Check if next button exists and is not disabled
                        next_button = await self.page.query_selector(selector)
                        if next_button:
                            # Check if button is disabled
                            is_disabled = await next_button.get_attribute("disabled")
                            aria_disabled = await next_button.get_attribute("aria-disabled")
                            
                            if is_disabled == "true" or aria_disabled == "true":
                                logger.info(f"Next button found but disabled with selector: {selector}")
                                break
                            
                            # Click the next button
                            logger.info(f"Found and clicking next button with selector: {selector}")
                            await next_button.click()
                            next_button_found = True
                            
                            # Wait for the page to load new content
                            logger.debug("Waiting for new page content to load...")
                            try:
                                # Wait for table to update (might need to adjust selector)
                                await self.page.wait_for_load_state("networkidle", timeout=10000)
                                await self.page.wait_for_selector("table.forceRecordLayout", timeout=10000)
                                # Additional wait to ensure content is fully rendered
                                await self.page.wait_for_timeout(2000)
                            except Exception as e:
                                logger.warning(f"Timeout waiting for new page content: {e}")
                            
                            page_number += 1
                            break
                            
                    except Exception as e:
                        logger.debug(f"Pagination selector {selector} failed: {e}")
                        continue
                
                # If no next button found or it's disabled, we're done
                if not next_button_found:
                    logger.info("No more pages found - pagination complete")
                    break
                
                # Safety check to prevent infinite loops
                if page_number > max_pages:
                    logger.warning(f"Reached maximum page limit ({max_pages}), stopping pagination")
                    break

            logger.info(f"Successfully scraped {len(all_rentals)} total rentals across {page_number} page(s)")
            return all_rentals

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
