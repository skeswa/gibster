import asyncio
import re
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional, cast

from bs4 import BeautifulSoup, Tag
from playwright.async_api import Browser, Page, async_playwright
from sqlalchemy.orm import Session

from .auth import decrypt_credential
from .logging_config import get_logger
from .models import Booking, User

if TYPE_CHECKING:
    from .sync_logger import SyncJobLogger

# Configure logging
logger = get_logger("scraper")

LOGIN_URL = "https://gibney.my.site.com/s/login"
RENTALS_URL = "https://gibney.my.site.com/s/booking-item"

# Timeout constants (in milliseconds)
DEFAULT_TIMEOUT = 20000  # 20 seconds (reduced from 30)
LOGIN_REDIRECT_TIMEOUT = 30000  # 30 seconds for login redirect (reduced from 60)
PAGE_LOAD_TIMEOUT = 25000  # 25 seconds for page loads (reduced from 45)
NAVIGATION_TIMEOUT = 30000  # 30 seconds for navigation (reduced from 60)
ELEMENT_TIMEOUT = 10000  # 10 seconds for element operations
NETWORK_IDLE_TIMEOUT = 5000  # 5 seconds for network idle (reduced from 10)


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
            start_time = datetime.now(timezone.utc)
            end_time = datetime.now(timezone.utc)

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
    def __init__(
        self, headless: bool = True, sync_logger: Optional["SyncJobLogger"] = None
    ):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.sync_logger = sync_logger
        self._table_selector = "table.forceRecordLayout"  # Default selector
        logger.info(f"Initializing Gibney scraper (headless: {headless})")

        if self.sync_logger:
            self.sync_logger.info("Initializing Gibney scraper", headless=headless)

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
            # Launch browser with better configuration for slow sites
            self.browser = await playwright.chromium.launch(
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-web-security",
                    "--disable-features=IsolateOrigins,site-per-process",
                ],
            )
            # Create page with default timeout
            self.page = await self.browser.new_page()
            self.page.set_default_timeout(DEFAULT_TIMEOUT)
            self.page.set_default_navigation_timeout(NAVIGATION_TIMEOUT)

            logger.info("Navigating to login page...")
            if self.sync_logger:
                self.sync_logger.log_scraper_event(
                    "navigation", "Navigating to login page", url=LOGIN_URL
                )

            login_start_time = datetime.now(timezone.utc)

            # Navigate to login page with extended timeout
            try:
                await self.page.goto(
                    LOGIN_URL, timeout=PAGE_LOAD_TIMEOUT, wait_until="domcontentloaded"
                )
            except Exception as e:
                logger.error(f"Failed to load login page: {e}")
                if self.sync_logger:
                    self.sync_logger.error("Failed to navigate to login page", error=e)
                raise GibneyScrapingError(
                    f"Unable to reach Gibney website. The site may be down or experiencing issues."
                )

            if self.sync_logger:
                self.sync_logger.log_timing("Login page navigation", login_start_time)

            # Fill login form
            logger.debug("Filling login form")
            if self.sync_logger:
                self.sync_logger.info("Filling login credentials")

            # The Gibney login page uses type-based selectors, not name attributes
            # First wait for the form to be fully loaded
            logger.debug("Waiting for login form to be visible...")
            await self.page.wait_for_selector(
                'input[type="text"]', state="visible", timeout=ELEMENT_TIMEOUT
            )
            await self.page.wait_for_selector(
                'input[type="password"]', state="visible", timeout=ELEMENT_TIMEOUT
            )

            print(f"[DEBUG] email: {email}")
            print(f"[DEBUG] password: {password}")

            # Fill the form fields - use placeholder attributes as backup selectors
            logger.debug("Filling username field...")
            await self.page.fill(
                'input[type="text"][placeholder="Username"], input[type="text"].inputBox',
                email,
            )
            logger.debug("Filling password field...")
            await self.page.fill(
                'input[type="password"][placeholder="Password"], input[type="password"].inputBox',
                password,
            )

            # Submit form - try multiple selectors since the button might not have type="submit"
            logger.info("Submitting login form...")
            if self.sync_logger:
                self.sync_logger.info("Attempting to submit login form")

            # Try different button selectors in order of preference
            # Based on actual HTML: <button class="slds-button slds-button--brand loginButton uiButton--none uiButton">
            button_selectors = [
                "button.loginButton",  # Primary selector based on HTML
                'button:has-text("Log in")',  # Text-based selector
                'button[class*="loginButton"]',
                "button.slds-button--brand",
                "button.uiButton",
                'button[type="submit"]',  # Generic fallback
                'button[aria-label*="Log in"]',
            ]

            button_clicked = False
            for selector in button_selectors:
                try:
                    logger.debug(f"Trying button selector: {selector}")
                    await self.page.click(selector, timeout=ELEMENT_TIMEOUT)
                    button_clicked = True
                    logger.debug(
                        f"Successfully clicked button with selector: {selector}"
                    )
                    # Give the page a moment to start processing the login
                    await self.page.wait_for_timeout(1000)
                    break
                except Exception as e:
                    logger.debug(f"Button selector {selector} failed: {e}")
                    continue

            if not button_clicked:
                # Log current page state for debugging
                logger.error("Failed to click login button, capturing page state...")
                try:
                    # Take a screenshot for debugging
                    screenshot_path = f"debug_login_failure_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    await self.page.screenshot(path=screenshot_path)
                    logger.info(f"Saved debug screenshot to {screenshot_path}")

                    # Check for error messages on the page
                    error_selectors = [
                        ".error",
                        '[class*="error"]',
                        '[role="alert"]',
                        ".slds-text-color_error",
                    ]
                    for error_sel in error_selectors:
                        try:
                            error_elem = await self.page.query_selector(error_sel)
                            if error_elem:
                                error_text = await error_elem.text_content()
                                logger.error(
                                    f"Found error message on page: {error_text}"
                                )
                                break
                        except:
                            pass
                except Exception as debug_error:
                    logger.error(f"Failed to capture debug info: {debug_error}")

                error_msg = "Could not find or click login button with any selector"
                if self.sync_logger:
                    self.sync_logger.error(error_msg, selectors_tried=button_selectors)
                raise GibneyScrapingError(error_msg)

            # Wait for redirect to home page after login
            logger.debug("Waiting for login redirect to home page...")
            if self.sync_logger:
                self.sync_logger.info("Waiting for login redirect")

            try:
                # Wait for redirect with multiple strategies
                redirect_success = False

                # Strategy 1: Wait for URL change away from login page
                login_wait_start = datetime.now(timezone.utc)
                try:
                    # Wait for navigation away from login page
                    await self.page.wait_for_function(
                        "() => !window.location.href.includes('/login')",
                        timeout=LOGIN_REDIRECT_TIMEOUT,
                    )
                    redirect_success = True
                    logger.debug(
                        f"Successfully navigated away from login page to: {self.page.url}"
                    )
                except Exception as e:
                    logger.debug(f"URL change wait failed: {e}")

                    # Strategy 2: Check if we're already on the right page or a variant
                    current_url = self.page.url
                    if (
                        "gibney.my.site.com/s/" in current_url
                        and "/login" not in current_url
                    ):
                        redirect_success = True
                        logger.debug(f"Already on expected page: {current_url}")
                    else:
                        # Strategy 3: Wait for specific elements that appear after login
                        try:
                            # Try multiple post-login indicators
                            post_login_selectors = [
                                'a:has-text("My Rentals")',
                                "nav",
                                '[class*="navigation"]',
                                'a[href*="booking"]',
                                ".slds-context-bar",
                                'button:has-text("Menu")',
                            ]

                            for selector in post_login_selectors:
                                try:
                                    await self.page.wait_for_selector(
                                        selector, timeout=5000, state="visible"
                                    )
                                    redirect_success = True
                                    logger.debug(
                                        f"Found post-login element: {selector}"
                                    )
                                    break
                                except:
                                    continue

                        except Exception:
                            pass

                        # Strategy 4: Check for login form disappearance
                        if not redirect_success:
                            try:
                                # If login form is gone, we likely logged in
                                await self.page.wait_for_selector(
                                    'input[type="password"]',
                                    state="hidden",
                                    timeout=5000,
                                )
                                redirect_success = True
                                logger.debug(
                                    "Login form disappeared, assuming successful login"
                                )
                            except:
                                pass

                # Log timing
                login_wait_duration = (
                    datetime.now(timezone.utc) - login_wait_start
                ).total_seconds()
                logger.debug(
                    f"Login redirect wait took {login_wait_duration:.2f} seconds"
                )

                if redirect_success:
                    logger.debug("Successfully logged in")
                    if self.sync_logger:
                        self.sync_logger.info("Login successful")
                        self.sync_logger.log_timing("Login process", login_start_time)
                else:
                    # Check if we're still on login page with error
                    current_url = self.page.url
                    if "/login" in current_url:
                        # Look for error messages that indicate wrong credentials
                        error_messages = []
                        error_selectors = [
                            ".error",
                            '[class*="error"]',
                            '[role="alert"]',
                            ".slds-text-color_error",
                            'div:has-text("Invalid username or password")',
                            'div:has-text("Your login attempt has failed")',
                        ]

                        for selector in error_selectors:
                            try:
                                error_elem = await self.page.query_selector(selector)
                                if error_elem:
                                    error_text = await error_elem.text_content()
                                    if error_text and error_text.strip():
                                        error_messages.append(error_text.strip())
                            except:
                                pass

                        if error_messages:
                            error_msg = f"Login failed: {'; '.join(error_messages)}"
                            logger.error(error_msg)
                            raise GibneyScrapingError(
                                f"Invalid credentials. Please check your Gibney username and password."
                            )
                        else:
                            # Save debug info
                            try:
                                screenshot_path = f"debug_login_stuck_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                                await self.page.screenshot(path=screenshot_path)
                                logger.info(
                                    f"Saved debug screenshot to {screenshot_path}"
                                )
                            except:
                                pass
                            raise GibneyScrapingError(
                                "Login failed - stuck on login page. The site may have changed its login process."
                            )
                    else:
                        raise GibneyScrapingError(
                            f"Login redirect failed - ended up on unexpected page: {current_url}"
                        )

            except Exception as e:
                if self.sync_logger:
                    self.sync_logger.error(
                        "Login failed - timeout or redirect issue", error=e
                    )
                # Check if it's a timeout issue
                if "timeout" in str(e).lower():
                    raise GibneyScrapingError(
                        "Login timed out. The Gibney website is responding slowly. Please try again later."
                    )
                else:
                    raise

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
                    await self.page.click(selector, timeout=ELEMENT_TIMEOUT)
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
                await self.page.goto(
                    RENTALS_URL,
                    wait_until="domcontentloaded",
                    timeout=NAVIGATION_TIMEOUT,
                )
                # Give the page time to load
                await self.page.wait_for_timeout(2000)
            else:
                # Wait for navigation after clicking My Rentals
                logger.debug("Waiting for navigation after clicking My Rentals...")
                navigation_start = datetime.now(timezone.utc)

                try:
                    # Use a shorter timeout for initial navigation
                    SHORT_NAV_TIMEOUT = 10000  # 10 seconds

                    # Wait for any navigation to occur
                    await self.page.wait_for_load_state(
                        "domcontentloaded", timeout=SHORT_NAV_TIMEOUT
                    )

                    # Check current URL immediately
                    current_url = self.page.url
                    logger.debug(f"Navigated to: {current_url}")

                    # Check if we're on any booking-related page
                    if (
                        "booking" in current_url
                        or "rental" in current_url
                        or "/s/" in current_url
                    ):
                        # We're on a valid page, wait briefly for content to load
                        try:
                            # Try to wait for table or other booking indicators
                            await self.page.wait_for_selector(
                                "table, [class*='booking'], [class*='rental']",
                                timeout=5000,
                                state="visible",
                            )
                            logger.info("Successfully navigated to booking page")
                        except:
                            # Even if selector fails, we're on the right page
                            logger.debug(
                                "On booking page but couldn't find specific elements"
                            )

                        navigation_duration = (
                            datetime.now(timezone.utc) - navigation_start
                        ).total_seconds()
                        logger.debug(
                            f"Navigation completed in {navigation_duration:.2f} seconds"
                        )
                    else:
                        # We're not on a booking page, try direct navigation
                        logger.warning(
                            f"Unexpected page after My Rentals click: {current_url}"
                        )
                        logger.info("Navigating directly to rentals page...")
                        await self.page.goto(
                            RENTALS_URL,
                            wait_until="domcontentloaded",
                            timeout=PAGE_LOAD_TIMEOUT,
                        )

                except Exception as nav_error:
                    # Navigation failed completely
                    current_url = self.page.url
                    logger.warning(
                        f"Navigation issue detected. Current URL: {current_url}, Error: {nav_error}"
                    )

                    # If we're already on a booking page despite the error, continue
                    if "booking" in current_url or "rental" in current_url:
                        logger.info(
                            "Already on a booking-related page despite navigation error, proceeding..."
                        )
                    else:
                        # Last resort: direct navigation
                        logger.warning(
                            "Attempting direct navigation to rentals page..."
                        )
                        try:
                            await self.page.goto(
                                RENTALS_URL,
                                wait_until="domcontentloaded",
                                timeout=PAGE_LOAD_TIMEOUT,
                            )
                        except Exception as goto_error:
                            logger.error(f"Direct navigation also failed: {goto_error}")
                            raise GibneyScrapingError(
                                "Unable to navigate to rentals page"
                            )

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
            if self.sync_logger:
                self.sync_logger.info("Starting rental data scraping")

            scraping_start_time = datetime.now(timezone.utc)

            # Navigate to rentals page if not already there
            if RENTALS_URL not in self.page.url:
                logger.debug("Navigating to rentals page")
                if self.sync_logger:
                    self.sync_logger.log_scraper_event(
                        "navigation", "Navigating to rentals page", url=RENTALS_URL
                    )
                await self.page.goto(
                    RENTALS_URL,
                    wait_until="domcontentloaded",
                    timeout=NAVIGATION_TIMEOUT,
                )

                # Wait for the page to be fully loaded
                try:
                    await self.page.wait_for_load_state(
                        "networkidle", timeout=NETWORK_IDLE_TIMEOUT
                    )
                except Exception as e:
                    logger.debug(f"Network idle timeout (non-critical): {e}")

            # Wait for page to load and check what we're actually on
            current_url = self.page.url
            logger.info(f"Current URL before waiting for table: {current_url}")

            # Wait for page to load with multiple selector strategies
            logger.debug("Waiting for rental table to load")
            table_selectors = [
                "table.forceRecordLayout",
                "table[class*='slds-table']",  # Salesforce Lightning Design System table
                "table[class*='rental']",
                "table[class*='booking']",
                "table",  # Generic fallback
            ]

            table_found = False
            for selector in table_selectors:
                try:
                    logger.debug(f"Trying table selector: {selector}")
                    await self.page.wait_for_selector(selector, timeout=5000)
                    logger.info(f"Found table with selector '{selector}'")
                    table_found = True
                    # Store the successful selector for later use
                    self._table_selector = selector
                    break
                except Exception:
                    continue

            if not table_found:
                logger.error("Failed to find any suitable table selector")

                # Take screenshot for debugging
                try:
                    screenshot_path = f"debug_rentals_page_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    await self.page.screenshot(path=screenshot_path)
                    logger.info(f"Saved debug screenshot to {screenshot_path}")
                except Exception as screenshot_error:
                    logger.error(f"Failed to save screenshot: {screenshot_error}")

                # Save HTML for debugging
                try:
                    html_content = await self.page.content()
                    html_path = f"debug_rentals_page_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                    with open(html_path, "w", encoding="utf-8") as f:
                        f.write(html_content)
                    logger.info(f"Saved debug HTML to {html_path}")

                    # Log what we can see on the page
                    soup = BeautifulSoup(html_content, "lxml")
                    tables = soup.find_all("table")
                    logger.info(f"Found {len(tables)} tables on the page")
                    for i, table in enumerate(tables[:5]):  # Log first 5 tables
                        if isinstance(table, Tag):
                            classes = table.get("class")
                            logger.info(
                                f"  Table {i}: classes={classes if classes else 'No classes'}"
                            )
                except Exception as html_error:
                    logger.error(f"Failed to save debug HTML: {html_error}")

                # Raise a more descriptive error
                raise GibneyScrapingError(
                    f"Could not find rental table on page. Current URL: {current_url}"
                )

            all_rentals = []
            page_number = 1
            max_pages = 100  # Safety limit to prevent infinite loops

            while page_number <= max_pages:
                logger.info(f"Scraping page {page_number}...")
                if self.sync_logger:
                    self.sync_logger.info(f"Processing page {page_number} of bookings")

                # Get page content
                content = await self.page.content()
                soup = BeautifulSoup(content, "lxml")

                # Debug: Check what tables are available (only log on first page)
                if page_number == 1:
                    all_tables = soup.select("table")
                    logger.debug(f"Found {len(all_tables)} tables on the page")
                    for j, table in enumerate(all_tables):
                        table_classes_raw: Any = table.get("class") or []
                        table_classes: List[str] = (
                            table_classes_raw
                            if isinstance(table_classes_raw, list)
                            else []
                        )
                        logger.debug(f"  Table {j}: classes={table_classes}")

                rows = soup.select(f"{self._table_selector} tbody tr")

                logger.info(
                    f"Found {len(rows)} rental rows to process on page {page_number}"
                )

                # If no rows found, try alternative selectors
                if len(rows) == 0:
                    logger.warning(
                        "No rows found with primary selector, trying alternatives..."
                    )
                    alternative_selectors = [
                        "table tbody tr",
                        f"{self._table_selector} tbody tr",
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
                        record_id_match = re.search(
                            r"Id=([a-zA-Z0-9]+)", href
                        ) or re.search(r"/([a-zA-Z0-9]{15,18})/", href)
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
                                    end_dt = datetime.strptime(
                                        end_time_str, date_format
                                    )
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
                                start_dt = datetime.now(timezone.utc)
                                end_dt = datetime.now(timezone.utc)
                            else:
                                logger.debug(
                                    f"Parsed dates successfully: {start_dt} to {end_dt}"
                                )

                        except Exception as e:
                            logger.warning(
                                f"Exception during date parsing for {rental_name}: {e}"
                            )
                            # Use current time as fallback
                            start_dt = datetime.now(timezone.utc)
                            end_dt = datetime.now(timezone.utc)

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
                logger.info(
                    f"Scraped {len(page_rentals)} rentals from page {page_number}"
                )
                if self.sync_logger:
                    self.sync_logger.info(
                        f"Found {len(page_rentals)} bookings on page {page_number}",
                        page_number=page_number,
                        bookings_on_page=len(page_rentals),
                        total_bookings_so_far=len(all_rentals),
                    )

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
                    "button.nextButton",
                    "a.next-page",
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
                            aria_disabled = await next_button.get_attribute(
                                "aria-disabled"
                            )

                            if is_disabled == "true" or aria_disabled == "true":
                                logger.info(
                                    f"Next button found but disabled with selector: {selector}"
                                )
                                break

                            # Click the next button
                            logger.info(
                                f"Found and clicking next button with selector: {selector}"
                            )
                            await next_button.click()
                            next_button_found = True

                            # Wait for the page to load new content
                            logger.debug("Waiting for new page content to load...")
                            try:
                                # Wait for table to update (might need to adjust selector)
                                await self.page.wait_for_load_state(
                                    "networkidle", timeout=NETWORK_IDLE_TIMEOUT
                                )
                                await self.page.wait_for_selector(
                                    self._table_selector, timeout=ELEMENT_TIMEOUT
                                )
                                # Additional wait to ensure content is fully rendered
                                await self.page.wait_for_timeout(2000)
                            except Exception as e:
                                logger.warning(
                                    f"Timeout waiting for new page content: {e}"
                                )

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
                    logger.warning(
                        f"Reached maximum page limit ({max_pages}), stopping pagination"
                    )
                    break

            logger.info(
                f"Successfully scraped {len(all_rentals)} total rentals across {page_number} page(s)"
            )
            return all_rentals

        except Exception as e:
            logger.error(f"Failed to scrape rentals: {e}")
            raise GibneyScrapingError(f"Failed to scrape rentals: {e}")


async def scrape_user_bookings(
    db: Session, user: User, sync_logger: Optional["SyncJobLogger"] = None
) -> List[Booking]:
    """Scrape bookings for a specific user and update the database"""
    logger.info(f"Starting booking scrape for user: {user.email}")

    if sync_logger:
        sync_logger.info("Starting booking scrape", user_email=user.email)

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
        async with GibneyScraper(headless=True, sync_logger=sync_logger) as scraper:
            await scraper.login(gibney_email, gibney_password)
            rental_data = await scraper.scrape_rentals()

        logger.info(
            f"Scraped {len(rental_data)} rentals from Gibney for user: {user.email}"
        )

        if sync_logger:
            sync_logger.info(f"Processing {len(rental_data)} bookings from Gibney")

        # Convert to Booking objects and update database
        updated_bookings = []
        created_count = 0
        updated_count = 0
        unchanged_count = 0

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
            if sync_logger:
                sync_logger.log_booking_processed(
                    str(old_booking.id),
                    str(old_booking.name),
                    "deleted",
                    reason="No longer in Gibney data",
                )
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
                    # Check if booking has actually changed
                    changed = False
                    for key, value in booking_data.items():
                        if key != "id" and getattr(existing_booking, key) != value:
                            changed = True
                            setattr(existing_booking, key, value)

                    setattr(existing_booking, "last_seen", datetime.now(timezone.utc))
                    updated_bookings.append(existing_booking)

                    if changed:
                        updated_count += 1
                        logger.debug(
                            f"Updated existing booking: {booking_data['name']}"
                        )
                        if sync_logger:
                            sync_logger.log_booking_processed(
                                booking_data["id"],
                                booking_data["name"],
                                "updated",
                                studio=booking_data["studio"],
                                start_time=booking_data["start_time"],
                            )
                    else:
                        unchanged_count += 1
                        logger.debug(f"Booking unchanged: {booking_data['name']}")
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
                        last_seen=datetime.now(timezone.utc),
                    )
                    db.add(new_booking)
                    updated_bookings.append(new_booking)
                    created_count += 1
                    logger.debug(f"Created new booking: {booking_data['name']}")
                    if sync_logger:
                        sync_logger.log_booking_processed(
                            booking_data["id"],
                            booking_data["name"],
                            "created",
                            studio=booking_data["studio"],
                            start_time=booking_data["start_time"],
                        )

            except Exception as e:
                logger.error(
                    f"Failed to process booking {booking_data.get('name', 'unknown')}: {e}"
                )
                continue

        # Commit changes
        db.commit()

        logger.info(f"Updated {len(updated_bookings)} bookings for user {user.email}")

        if sync_logger:
            sync_logger.log_sync_summary(
                total_bookings=len(rental_data),
                created=created_count,
                updated=updated_count,
                unchanged=unchanged_count,
                errors=0,
            )

        return updated_bookings

    except Exception as e:
        logger.error(f"Failed to scrape bookings for user {user.email}: {e}")
        if sync_logger:
            sync_logger.error(f"Scraping failed: {str(e)}", error=e)
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
