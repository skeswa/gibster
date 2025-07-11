import asyncio
import hashlib
import json
import re
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional, cast

from bs4 import BeautifulSoup, Tag
from playwright.async_api import Browser, Page, async_playwright
from sqlalchemy.orm import Session

from auth import decrypt_credential
from logging_config import get_logger
from models import Booking, User

if TYPE_CHECKING:
    from sync_logger import SyncJobLogger

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

# Batch processing constants
BATCH_SIZE = 100  # Process bookings in batches of 100


def create_booking_hash(booking_data: Dict[str, Any]) -> str:
    """Create a hash of booking data for efficient change detection"""
    # Include only fields that matter for change detection
    relevant_fields = {
        "name": booking_data.get("name"),
        "start_time": str(booking_data.get("start_time")),
        "end_time": str(booking_data.get("end_time")),
        "studio": booking_data.get("studio"),
        "location": booking_data.get("location"),
        "status": booking_data.get("status"),
        "price": float(booking_data.get("price", 0)),
    }

    # Create a deterministic JSON string
    json_str = json.dumps(relevant_fields, sort_keys=True)

    # Return hash
    return hashlib.sha256(json_str.encode()).hexdigest()


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
                    break
                except Exception as e:
                    logger.debug(f"Button selector {selector} failed: {e}")
                    continue

            if not button_clicked:
                # Log current page state for debugging
                logger.error("Failed to click login button, capturing page state...")
                try:
                    # Log page state for debugging
                    current_url = self.page.url
                    logger.error(
                        f"Login button click failed. Current URL: {current_url}"
                    )

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
                            # Log debug info
                            try:
                                current_url = self.page.url
                                logger.info(
                                    f"Login may be stuck. Current URL: {current_url}"
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

    async def scrape_rentals(
        self, max_rentals: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Scrape rental data from the rentals page, handling infinite scroll

        This method will:
        1. Navigate to the rentals page if not already there
        2. Scrape all bookings from the current view
        3. Scroll to the bottom to trigger infinite scroll loading
        4. Wait for new content to load (spinner to disappear)
        5. Continue scrolling until no new content loads
        6. Return all bookings from the entire scrollable list

        Args:
            max_rentals: Optional limit on number of rentals to scrape (useful for testing)

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

            if table_found:
                # Wait a bit for the table content to stabilize
                logger.debug("Table found, waiting for content to stabilize...")
                await self.page.wait_for_timeout(1000)
            else:
                logger.error("Failed to find any suitable table selector")

                # Log page state for debugging
                try:
                    current_url = self.page.url
                    logger.info(
                        f"On rentals page for debugging. Current URL: {current_url}"
                    )
                except Exception as url_error:
                    logger.error(f"Failed to get current URL: {url_error}")

                # Get HTML for debugging analysis
                try:
                    html_content = await self.page.content()
                    # Log first 500 chars of HTML for debugging
                    logger.debug(
                        f"Page HTML preview (first 500 chars): {html_content[:500]}..."
                    )

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
            processed_ids: set[str] = set()  # Track IDs to avoid duplicates
            max_scroll_attempts = 50  # Safety limit to prevent infinite scrolling
            scroll_count = 0
            last_row_count = 0
            no_new_content_count = 0
            # Increased threshold for more patient scrolling
            MAX_NO_NEW_CONTENT_ATTEMPTS = 4  # Increased from 2 to 4

            # Log initial state
            logger.info(
                f"Starting infinite scroll scraping (max attempts: {max_scroll_attempts})"
            )

            while scroll_count < max_scroll_attempts:
                scroll_start_time = datetime.now(timezone.utc)
                logger.info(
                    f"Processing content (scroll attempt {scroll_count + 1})..."
                )
                if self.sync_logger:
                    self.sync_logger.info(
                        f"Processing bookings (scroll {scroll_count + 1})"
                    )

                # Get current page content
                content = await self.page.content()
                soup = BeautifulSoup(content, "lxml")

                # Get all rows currently visible
                rows = soup.select(f"{self._table_selector} tbody tr")
                current_row_count = len(rows)

                # If no rows found on first attempt, try alternative selectors
                if current_row_count == 0 and scroll_count == 0:
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
                            current_row_count = len(rows)
                            logger.info(
                                f"Using alternative selector '{alt_selector}' with {current_row_count} rows"
                            )
                            break

                logger.info(
                    f"Found {current_row_count} total rows in DOM "
                    f"(previous: {last_row_count}, processed IDs: {len(processed_ids)})"
                )

                # Process all visible rows
                new_rentals_count = 0
                for i, row in enumerate(rows):
                    cells = row.select("th, td")
                    if not cells or len(cells) < 8:
                        continue

                    try:
                        # Extract rental link to get ID
                        rental_link = cells[1].select_one("a")
                        if not rental_link:
                            continue

                        # Extract record ID
                        href = str(rental_link.get("href", ""))
                        record_id_match = re.search(
                            r"Id=([a-zA-Z0-9]+)", href
                        ) or re.search(r"/([a-zA-Z0-9]{15,18})/", href)

                        rental_name = rental_link.get_text(strip=True)
                        record_id = (
                            record_id_match.group(1)
                            if record_id_match
                            else f"unknown_{rental_name}_{i}"
                        )

                        # Skip if we've already processed this booking
                        if record_id in processed_ids:
                            continue

                        processed_ids.add(record_id)
                        new_rentals_count += 1

                        # Extract all booking data
                        start_time_str = cells[2].get_text(strip=True)
                        end_time_str = cells[3].get_text(strip=True)
                        studio = cells[4].get_text(strip=True)
                        price_str = cells[5].get_text(strip=True)
                        status = cells[6].get_text(strip=True)
                        location = cells[7].get_text(strip=True)

                        # Parse dates with multiple format support
                        date_formats = [
                            "%m/%d/%Y %I:%M %p",  # 6/9/2025 7:00 PM
                            "%b %d, %Y %I:%M %p",  # Jun 26, 2025 5:01 PM
                            "%m/%d/%Y %H:%M",  # 6/9/2025 19:00
                            "%Y-%m-%d %H:%M:%S",  # 2025-06-09 19:00:00
                            "%Y-%m-%dT%H:%M:%S",  # 2025-06-09T19:00:00
                        ]

                        start_dt = None
                        end_dt = None

                        for date_format in date_formats:
                            try:
                                start_dt = datetime.strptime(
                                    start_time_str, date_format
                                ).replace(tzinfo=timezone.utc)
                                end_dt = datetime.strptime(
                                    end_time_str, date_format
                                ).replace(tzinfo=timezone.utc)
                                break
                            except ValueError:
                                continue

                        if start_dt is None or end_dt is None:
                            logger.warning(
                                f"Failed to parse dates for {rental_name}: start='{start_time_str}', end='{end_time_str}'"
                            )
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

                        all_rentals.append(rental)
                        logger.debug(f"Scraped rental: {rental_name}")

                    except Exception as e:
                        logger.warning(f"Skipping row {i+1} due to parsing error: {e}")
                        continue

                logger.info(
                    f"Processed {new_rentals_count} new rentals in this scroll. Total: {len(all_rentals)}"
                )
                if self.sync_logger:
                    self.sync_logger.info(
                        f"Found {new_rentals_count} new bookings",
                        scroll_attempt=scroll_count + 1,
                        total_bookings=len(all_rentals),
                    )

                # Check if we got new content
                if current_row_count == last_row_count:
                    no_new_content_count += 1
                    logger.info(
                        f"No new rows loaded (attempt {no_new_content_count}/{MAX_NO_NEW_CONTENT_ATTEMPTS}). "
                        f"Current total: {current_row_count} rows, {len(all_rentals)} unique bookings"
                    )
                    logger.debug(
                        f"Current row count: {current_row_count}, Last row count: {last_row_count}"
                    )

                    # If no new content after multiple attempts, we're done
                    if no_new_content_count >= MAX_NO_NEW_CONTENT_ATTEMPTS:
                        logger.info(
                            f"No new content after {MAX_NO_NEW_CONTENT_ATTEMPTS} attempts at row count {current_row_count}, "
                            f"total unique bookings: {len(all_rentals)}. Assuming all data loaded."
                        )
                        # Log scroll state when stopping
                        if no_new_content_count == MAX_NO_NEW_CONTENT_ATTEMPTS:
                            try:
                                scroll_position = await self.page.evaluate(
                                    "window.scrollY"
                                )
                                page_height = await self.page.evaluate(
                                    "document.body.scrollHeight"
                                )
                                logger.info(
                                    f"Stopping scroll at position {scroll_position}/{page_height}"
                                )
                            except Exception as e:
                                logger.debug(f"Failed to get scroll position: {e}")
                        break
                else:
                    rows_added = current_row_count - last_row_count
                    logger.debug(
                        f"Loaded {rows_added} new rows (total now: {current_row_count})"
                    )
                    no_new_content_count = 0
                    last_row_count = current_row_count

                # Scroll to bottom to trigger infinite scroll
                logger.debug("Scrolling to bottom to trigger infinite scroll...")

                # Multiple scroll attempts to ensure the event is registered
                for scroll_attempt in range(3):
                    # Scroll to the bottom of the page
                    await self.page.evaluate(
                        "window.scrollTo(0, document.body.scrollHeight)"
                    )

                    # Small delay between scroll attempts
                    if scroll_attempt < 2:
                        await self.page.wait_for_timeout(200)

                # Also try scrolling the table container if it exists
                try:
                    await self.page.evaluate(
                        """
                        // Find the table container that might have its own scroll
                        const tableContainers = document.querySelectorAll('[class*="slds-scrollable"], [style*="overflow"], .datatable-container, [class*="scroll"]');
                        tableContainers.forEach(container => {
                            container.scrollTop = container.scrollHeight;
                        });
                        
                        // Also try the table's parent elements
                        const table = document.querySelector('table');
                        if (table) {
                            let parent = table.parentElement;
                            while (parent && parent !== document.body) {
                                if (parent.scrollHeight > parent.clientHeight) {
                                    parent.scrollTop = parent.scrollHeight;
                                }
                                parent = parent.parentElement;
                            }
                        }
                        
                        // Trigger scroll events explicitly
                        window.dispatchEvent(new Event('scroll'));
                        document.dispatchEvent(new Event('scroll'));
                    """
                    )
                except Exception as e:
                    logger.debug(f"Table container scroll attempt failed: {e}")

                # Additional wait after scrolling to let the page register the scroll
                await self.page.wait_for_timeout(500)

                # Wait for potential spinner/loading indicator
                logger.debug("Checking for loading indicators...")

                # Look for common loading indicators
                loading_selectors = [
                    ".spinner",
                    '[class*="spinner"]',
                    '[class*="loading"]',
                    '[class*="slds-spinner"]',
                    ".slds-spinner_container",
                    '[role="status"]',
                    "lightning-spinner",
                ]

                # Use JavaScript to check all spinner selectors at once (much faster)
                spinner_check_script = """
                    () => {
                        const selectors = [
                            '.spinner',
                            '[class*="spinner"]',
                            '[class*="loading"]',
                            '[class*="slds-spinner"]',
                            '.slds-spinner_container',
                            '[role="status"]',
                            'lightning-spinner'
                        ];
                        
                        for (const selector of selectors) {
                            const elements = document.querySelectorAll(selector);
                            for (const el of elements) {
                                // Check if element is visible
                                if (el && el.offsetParent !== null && 
                                    (el.offsetWidth > 0 || el.offsetHeight > 0)) {
                                    return selector;
                                }
                            }
                        }
                        return null;
                    }
                """

                # First wait a bit for spinner to potentially appear after scroll
                await self.page.wait_for_timeout(300)

                # Check for spinner multiple times as it might appear with delay
                spinner_selector = None
                for spinner_check in range(3):
                    spinner_selector = await self.page.evaluate(spinner_check_script)
                    if spinner_selector:
                        break
                    if spinner_check < 2:  # Don't wait after last check
                        await self.page.wait_for_timeout(200)

                if spinner_selector:
                    logger.debug(f"Found loading indicator: {spinner_selector}")
                    # Wait for the specific spinner to disappear
                    try:
                        await self.page.wait_for_selector(
                            spinner_selector,
                            timeout=15000,  # Increased from 10s to 15s
                            state="hidden",
                        )
                        logger.debug("Loading indicator disappeared")
                        # Wait for DOM to stabilize after spinner
                        await self.page.wait_for_timeout(500)  # Increased from 200ms
                    except Exception as e:
                        logger.debug(f"Spinner wait timeout: {e}")
                else:
                    # No spinner visible, check if content changed
                    logger.debug(
                        "No loading indicator found, checking for content changes..."
                    )

                    # Wait for potential DOM changes with a progressive strategy
                    # Start with a longer wait time to give infinite scroll time to trigger
                    logger.debug("Waiting for infinite scroll to trigger...")

                    # First, wait a bit for the scroll event to register
                    await self.page.wait_for_timeout(500)

                    # Check multiple times for new content with increasing patience
                    content_check_attempts = 0
                    max_content_checks = 4  # Increased from 3
                    # More patient wait times, especially for the first check
                    check_intervals = [3000, 4000, 3000, 2000]  # Longer initial waits

                    new_content_found = False
                    for attempt in range(max_content_checks):
                        try:
                            await self.page.wait_for_function(
                                f"document.querySelectorAll('{self._table_selector} tbody tr').length > {current_row_count}",
                                timeout=check_intervals[attempt],
                            )
                            logger.debug(
                                f"New content detected on attempt {attempt + 1}"
                            )
                            new_content_found = True
                            break
                        except:
                            content_check_attempts += 1
                            logger.debug(
                                f"No new content yet (attempt {attempt + 1}/{max_content_checks}), "
                                f"waited {check_intervals[attempt]}ms"
                            )

                            # On intermediate attempts, try scrolling again
                            if attempt < max_content_checks - 1:
                                logger.debug("Retrying scroll to trigger load...")
                                # Try multiple scroll methods
                                await self.page.evaluate(
                                    "window.scrollTo(0, document.body.scrollHeight)"
                                )
                                await self.page.evaluate(
                                    "window.scrollBy(0, 100)"  # Small additional scroll
                                )
                                # Longer wait before next check
                                await self.page.wait_for_timeout(500)

                    if not new_content_found:
                        logger.debug("No new content detected after all attempts")

                # Check for "end of list" indicators
                try:
                    end_of_list_indicators = await self.page.evaluate(
                        """
                        () => {
                            // Check for common end-of-list messages
                            const endTexts = ['no more', 'end of', 'showing all', 'that\'s all'];
                            const pageText = document.body.innerText.toLowerCase();
                            
                            for (const text of endTexts) {
                                if (pageText.includes(text)) {
                                    return text;
                                }
                            }
                            
                            // Check if we're at the bottom of a scrollable container
                            const scrollContainers = document.querySelectorAll('[style*="overflow"]');
                            for (const container of scrollContainers) {
                                if (container.scrollHeight > 0 && 
                                    container.scrollTop + container.clientHeight >= container.scrollHeight - 5) {
                                    return 'at_bottom';
                                }
                            }
                            
                            return null;
                        }
                        """
                    )
                    if end_of_list_indicators:
                        logger.info(
                            f"Found end-of-list indicator: {end_of_list_indicators}"
                        )
                except Exception as e:
                    logger.debug(f"End-of-list check failed: {e}")

                scroll_count += 1

                # Log scroll performance
                scroll_duration = (
                    datetime.now(timezone.utc) - scroll_start_time
                ).total_seconds()
                logger.debug(f"Scroll iteration took {scroll_duration:.2f} seconds")

                # Check if we've reached the rental limit
                if max_rentals and len(all_rentals) >= max_rentals:
                    logger.info(f"Reached rental limit of {max_rentals}, stopping")
                    break

                # Safety check
                if scroll_count >= max_scroll_attempts:
                    logger.warning(
                        f"Reached maximum scroll attempts ({max_scroll_attempts}), stopping"
                    )
                    break

            # Log overall scraping performance
            total_scrape_duration = (
                datetime.now(timezone.utc) - scraping_start_time
            ).total_seconds()
            logger.info(
                f"Successfully scraped {len(all_rentals)} total rentals after {scroll_count} scroll attempts in {total_scrape_duration:.2f} seconds"
            )
            if self.sync_logger:
                self.sync_logger.log_timing(
                    "Rental scraping completed", scraping_start_time
                )

            # If max_rentals was specified, return only up to that limit
            if max_rentals and len(all_rentals) > max_rentals:
                return all_rentals[:max_rentals]

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

        # Start timing database operations
        db_start_time = datetime.now(timezone.utc)

        # Convert to Booking objects and update database
        updated_bookings = []
        created_count = 0
        updated_count = 0
        unchanged_count = 0

        # Bulk load all existing bookings for this user (1 query instead of N)
        load_start = datetime.now(timezone.utc)
        existing_bookings = {
            b.id: b for b in db.query(Booking).filter(Booking.user_id == user.id).all()
        }
        load_duration = (datetime.now(timezone.utc) - load_start).total_seconds()
        logger.debug(
            f"Loaded {len(existing_bookings)} existing bookings in {load_duration:.3f}s"
        )

        # Find bookings to delete (no longer in scraped data)
        scraped_ids = {booking["id"] for booking in rental_data}
        bookings_to_delete = [
            booking
            for booking_id, booking in existing_bookings.items()
            if booking_id not in scraped_ids
        ]

        # Delete old bookings
        if bookings_to_delete:
            delete_ids = [b.id for b in bookings_to_delete]
            db.query(Booking).filter(
                Booking.user_id == user.id, Booking.id.in_(delete_ids)
            ).delete(synchronize_session=False)

            for old_booking in bookings_to_delete:
                logger.info(f"Removing old booking: {old_booking.name}")
                if sync_logger:
                    sync_logger.log_booking_processed(
                        str(old_booking.id),
                        str(old_booking.name),
                        "deleted",
                        reason="No longer in Gibney data",
                    )

        # Prepare bulk operations
        bookings_to_insert = []
        bookings_to_update = []

        # Process scraped bookings
        for booking_data in rental_data:
            try:
                booking_id = booking_data["id"]
                existing_booking = existing_bookings.get(booking_id)

                if existing_booking:
                    # Use hash comparison for efficient change detection
                    existing_hash = existing_booking.create_hash()
                    new_hash = create_booking_hash(booking_data)
                    changed = existing_hash != new_hash

                    update_data = {"last_seen": datetime.now(timezone.utc)}

                    if changed:
                        # Only update fields if hash differs
                        for key, value in booking_data.items():
                            if key != "id":
                                update_data[key] = value
                        # Add to update batch
                        update_data["id"] = booking_id
                        bookings_to_update.append(update_data)
                        updated_count += 1
                        logger.debug(f"Booking changed: {booking_data['name']}")
                        if sync_logger:
                            sync_logger.log_booking_processed(
                                booking_data["id"],
                                booking_data["name"],
                                "updated",
                                studio=booking_data["studio"],
                                start_time=booking_data["start_time"].isoformat(),
                            )
                    else:
                        # Still update last_seen even if unchanged
                        bookings_to_update.append(
                            {"id": booking_id, "last_seen": datetime.now(timezone.utc)}
                        )
                        unchanged_count += 1
                        logger.debug(f"Booking unchanged: {booking_data['name']}")

                    updated_bookings.append(existing_booking)
                else:
                    # Prepare for bulk insert
                    insert_data = booking_data.copy()
                    insert_data["user_id"] = user.id
                    insert_data["last_seen"] = datetime.now(timezone.utc)
                    bookings_to_insert.append(insert_data)
                    created_count += 1
                    logger.debug(f"New booking to create: {booking_data['name']}")
                    if sync_logger:
                        sync_logger.log_booking_processed(
                            booking_data["id"],
                            booking_data["name"],
                            "created",
                            studio=booking_data["studio"],
                            start_time=booking_data["start_time"].isoformat(),
                        )

            except Exception as e:
                logger.error(
                    f"Failed to process booking {booking_data.get('name', 'unknown')}: {e}"
                )
                continue

        # Perform bulk operations in batches
        if bookings_to_insert:
            logger.debug(f"Bulk inserting {len(bookings_to_insert)} new bookings")
            # Process inserts in batches
            for i in range(0, len(bookings_to_insert), BATCH_SIZE):
                batch = bookings_to_insert[i : i + BATCH_SIZE]
                db.bulk_insert_mappings(Booking, batch)  # type: ignore[arg-type]
                db.commit()  # Commit each batch
                logger.debug(
                    f"Inserted batch {i//BATCH_SIZE + 1} ({len(batch)} bookings)"
                )

                # Add new bookings to updated_bookings list
                for insert_data in batch:
                    new_booking = Booking(**insert_data)
                    updated_bookings.append(new_booking)

        if bookings_to_update:
            logger.debug(f"Bulk updating {len(bookings_to_update)} existing bookings")
            # Process updates in batches
            for i in range(0, len(bookings_to_update), BATCH_SIZE):
                batch = bookings_to_update[i : i + BATCH_SIZE]
                db.bulk_update_mappings(Booking, batch)  # type: ignore[arg-type]
                db.commit()  # Commit each batch
                logger.debug(
                    f"Updated batch {i//BATCH_SIZE + 1} ({len(batch)} bookings)"
                )

        # Final commit for any remaining operations
        db.commit()

        # Log database operation performance
        db_duration = (datetime.now(timezone.utc) - db_start_time).total_seconds()
        logger.info(
            f"Database sync completed in {db_duration:.2f}s - "
            f"Created: {created_count}, Updated: {updated_count}, "
            f"Unchanged: {unchanged_count}, Deleted: {len(bookings_to_delete)}"
        )

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
