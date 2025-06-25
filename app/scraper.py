import re
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Page, Browser
from sqlalchemy.orm import Session

from .models import User, Booking
from .auth import decrypt_credential

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LOGIN_URL = "https://gibney.my.site.com/s/login"
RENTALS_URL = "https://gibney.my.site.com/s/booking-item"

def parse_booking_row(row_html: str) -> Dict[str, Any]:
    """Parse a booking row from HTML and extract booking data"""
    soup = BeautifulSoup(row_html, 'html.parser')
    
    # Find cells - this is a mock implementation based on expected structure
    cells = soup.find_all(['td', 'th'])
    
    if len(cells) < 7:
        raise ValueError("Invalid row format - not enough cells")
    
    # Extract link and name from first cell
    link_cell = cells[0]
    link = link_cell.find('a')
    if not link:
        raise ValueError("No booking link found")
    
    name = link.get_text(strip=True)
    href = link.get('href', '')
    
    # Extract booking ID from href
    id_match = re.search(r'Id=([a-zA-Z0-9]{15,18})', href)
    booking_id = id_match.group(1) if id_match else f"unknown_{name}"
    
    # Parse datetime strings (assuming format like "Jan 15, 2024 10:00 AM")
    start_time_str = cells[1].get_text(strip=True)
    end_time_str = cells[2].get_text(strip=True)
    
    try:
        start_time = datetime.strptime(start_time_str, "%b %d, %Y %I:%M %p")
        end_time = datetime.strptime(end_time_str, "%b %d, %Y %I:%M %p")
    except ValueError:
        # If parsing fails, use a default format
        start_time = datetime.now()
        end_time = datetime.now()
    
    studio = cells[3].get_text(strip=True)
    location = cells[4].get_text(strip=True)
    status = cells[5].get_text(strip=True)
    
    # Parse price
    price_str = cells[6].get_text(strip=True) if len(cells) > 6 else "$0.00"
    price = 0.0
    if price_str.startswith('$'):
        try:
            price = float(price_str[1:].replace(',', ''))
        except ValueError:
            price = 0.0
    
    # Build full URL
    record_url = f"https://gibney.my.site.com{href}" if href.startswith('/') else href
    
    return {
        "id": booking_id,
        "name": name,
        "start_time": start_time.strftime("%Y-%m-%dT%H:%M:%S"),
        "end_time": end_time.strftime("%Y-%m-%dT%H:%M:%S"),
        "studio": studio,
        "location": location,
        "status": status,
        "price": price,
        "record_url": record_url
    }

def parse_price(price_str: str) -> float:
    """Parse price string and return float value"""
    if not price_str or price_str.lower() == "free":
        return 0.0
    
    if price_str.startswith("$"):
        try:
            return float(price_str[1:].replace(',', ''))
        except ValueError:
            return 0.0
    
    try:
        return float(price_str)
    except ValueError:
        return 0.0

class GibneyScrapingError(Exception):
    """Raised when scraping fails"""
    pass

class GibneyScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            self.browser.close()
    
    def login(self, email: str, password: str) -> None:
        """Log into Gibney website"""
        try:
            playwright = sync_playwright().start()
            self.browser = playwright.chromium.launch(headless=self.headless)
            self.page = self.browser.new_page()
            
            logger.info("Navigating to login page...")
            self.page.goto(LOGIN_URL)
            
            # Fill login form
            self.page.fill('input[name="username"]', email)
            self.page.fill('input[name="password"]', password)
            
            # Submit form
            logger.info("Submitting login form...")
            self.page.click('button[type="submit"]')
            
            # Wait for redirect after login
            self.page.wait_for_url(f"{RENTALS_URL}**", timeout=30000)
            logger.info("Login successful")
            
        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise GibneyScrapingError(f"Failed to login: {e}")
    
    def scrape_rentals(self) -> List[Dict[str, Any]]:
        """Scrape rental data from the rentals page"""
        if not self.page:
            raise GibneyScrapingError("Must login first")
        
        try:
            logger.info("Scraping rentals data...")
            
            # Navigate to rentals page if not already there
            if RENTALS_URL not in self.page.url:
                self.page.goto(RENTALS_URL)
            
            # Wait for page to load
            self.page.wait_for_selector("table.forceRecordLayout", timeout=30000)
            
            # Get page content
            content = self.page.content()
            soup = BeautifulSoup(content, "lxml")
            
            rentals = []
            rows = soup.select("table.forceRecordLayout tbody tr")
            
            for row in rows:
                cells = row.select("th, td")
                if not cells or len(cells) < 8:
                    continue
                
                try:
                    # Extract data from each cell
                    rental_link = cells[1].select_one("a")
                    if not rental_link:
                        continue
                    
                    rental_name = rental_link.get_text(strip=True)
                    start_time_str = cells[2].get_text(strip=True)
                    end_time_str = cells[3].get_text(strip=True)
                    studio = cells[4].get_text(strip=True)
                    price_str = cells[5].get_text(strip=True)
                    status = cells[6].get_text(strip=True)
                    location = cells[7].get_text(strip=True)
                    
                    # Extract record ID from href
                    href = rental_link.get("href", "")
                    record_id_match = re.search(r'/([a-zA-Z0-9]{15,18})/', href)
                    record_id = record_id_match.group(1) if record_id_match else f"unknown_{rental_name}"
                    
                    # Parse dates
                    try:
                        start_dt = datetime.strptime(start_time_str, "%m/%d/%Y %I:%M %p")
                        end_dt = datetime.strptime(end_time_str, "%m/%d/%Y %I:%M %p")
                    except ValueError as e:
                        logger.warning(f"Failed to parse dates for {rental_name}: {e}")
                        continue
                    
                    # Parse price
                    price = None
                    if price_str and price_str.replace("$", "").replace(",", "").replace(".", "").isdigit():
                        try:
                            price = float(price_str.replace("$", "").replace(",", ""))
                        except ValueError:
                            pass
                    
                    # Build full URL
                    record_url = f"https://gibney.my.site.com{href}" if href.startswith("/") else href
                    
                    rental_data = {
                        "id": record_id,
                        "name": rental_name,
                        "start_time": start_dt,
                        "end_time": end_dt,
                        "studio": studio,
                        "location": location,
                        "status": status,
                        "price": price,
                        "record_url": record_url
                    }
                    
                    rentals.append(rental_data)
                    logger.debug(f"Scraped rental: {rental_name}")
                    
                except (AttributeError, IndexError, ValueError) as e:
                    logger.warning(f"Skipping row due to parsing error: {e}")
                    continue
            
            logger.info(f"Successfully scraped {len(rentals)} rentals")
            return rentals
            
        except Exception as e:
            logger.error(f"Failed to scrape rentals: {e}")
            raise GibneyScrapingError(f"Failed to scrape rentals: {e}")

def scrape_user_bookings(db: Session, user: User) -> List[Booking]:
    """Scrape bookings for a specific user and update the database"""
    if not user.gibney_email or not user.gibney_password:
        raise ValueError("User has no Gibney credentials")
    
    # Decrypt credentials
    gibney_email = decrypt_credential(user.gibney_email)
    gibney_password = decrypt_credential(user.gibney_password)
    
    # Scrape data
    with GibneyScraper() as scraper:
        scraper.login(gibney_email, gibney_password)
        rental_data = scraper.scrape_rentals()
    
    # Update database
    updated_bookings = []
    current_time = datetime.utcnow()
    
    for data in rental_data:
        # Skip canceled bookings
        if data["status"].lower() == "canceled":
            continue
        
        # Create or update booking
        booking = db.query(Booking).filter(Booking.id == data["id"], Booking.user_id == user.id).first()
        
        if booking:
            # Update existing booking
            booking.name = data["name"]
            booking.start_time = data["start_time"]
            booking.end_time = data["end_time"]
            booking.studio = data["studio"]
            booking.location = data["location"]
            booking.status = data["status"]
            booking.price = data["price"]
            booking.record_url = data["record_url"]
            booking.last_seen = current_time
        else:
            # Create new booking
            booking = Booking(
                id=data["id"],
                user_id=user.id,
                name=data["name"],
                start_time=data["start_time"],
                end_time=data["end_time"],
                studio=data["studio"],
                location=data["location"],
                status=data["status"],
                price=data["price"],
                record_url=data["record_url"],
                last_seen=current_time
            )
            db.add(booking)
        
        updated_bookings.append(booking)
    
    # Remove bookings that weren't seen (they may have been deleted/canceled)
    old_bookings = db.query(Booking).filter(
        Booking.user_id == user.id,
        Booking.last_seen < current_time
    ).all()
    
    for old_booking in old_bookings:
        db.delete(old_booking)
        logger.info(f"Removed old booking: {old_booking.name}")
    
    db.commit()
    logger.info(f"Updated {len(updated_bookings)} bookings for user {user.email}")
    
    return updated_bookings 