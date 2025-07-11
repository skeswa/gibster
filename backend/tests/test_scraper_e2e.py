"""
End-to-end tests for the Gibney scraper that test against the real website.
These tests should be run manually to verify scraper functionality.
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path to import scraper
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from scraper import GibneyScraper, GibneyScrapingError

# Try to load environment variables from backend/.env
try:
    from dotenv import load_dotenv

    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✓ Loaded environment variables from {env_path}")
except ImportError:
    print("⚠️  python-dotenv not installed, using system environment variables only")


async def test_gibney_login():
    """Test login functionality against real Gibney website"""
    print("\n=== Testing Gibney Login ===")

    # Get credentials from environment or prompt
    email = os.environ.get("TEST_GIBNEY_EMAIL")
    password = os.environ.get("TEST_GIBNEY_PASSWORD")

    if not email or not password:
        print("\n⚠️  No test credentials found!")
        print("\nYou can provide credentials in one of these ways:")
        print("1. Add to backend/.env file:")
        print("   TEST_GIBNEY_EMAIL=your-email@example.com")
        print("   TEST_GIBNEY_PASSWORD=your-password")
        print("\n2. Set environment variables:")
        print("   export TEST_GIBNEY_EMAIL='your-email@example.com'")
        print("   export TEST_GIBNEY_PASSWORD='your-password'")

        # Skip interactive input in CI environment
        if os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
            print("\n✗ Running in CI environment - interactive input not available")
            print(
                "Please set TEST_GIBNEY_EMAIL and TEST_GIBNEY_PASSWORD environment variables"
            )
            return False

        print("\n3. Enter them now:")
        email = input("   Gibney email: ").strip()
        password = input("   Gibney password: ").strip()

    if not email or not password:
        print("Error: Credentials required for testing")
        return False

    print(f"\nTesting login for: {email}")
    print("Starting scraper (headless=False for debugging)...")

    try:
        async with GibneyScraper(headless=False) as scraper:
            start_time = datetime.now()
            print("Attempting login...")

            await scraper.login(email, password)

            login_duration = (datetime.now() - start_time).total_seconds()
            print(f"✓ Login successful! (took {login_duration:.2f} seconds)")

            # Verify we're on the right page
            assert scraper.page is not None, "Page should be initialized after login"
            current_url = scraper.page.url
            print(f"Current URL: {current_url}")

            if "/login" in current_url:
                print("⚠️  Warning: Still on login page, login may have failed")
                return False

            # Try to find navigation elements
            print("\nVerifying post-login elements...")
            try:
                # Wait a bit for page to stabilize
                await scraper.page.wait_for_timeout(2000)

                # Look for common post-login elements
                selectors_to_check = [
                    ("My Rentals link", 'a:has-text("My Rentals")'),
                    ("Navigation bar", "nav"),
                    ("User menu", '[class*="userMenu"], [class*="user-menu"]'),
                    ("Logout link", 'a:has-text("Log Out"), a:has-text("Logout")'),
                ]

                found_elements = []
                for name, selector in selectors_to_check:
                    try:
                        element = await scraper.page.query_selector(selector)
                        if element:
                            found_elements.append(name)
                            print(f"  ✓ Found: {name}")
                        else:
                            print(f"  ✗ Not found: {name}")
                    except Exception as e:
                        print(f"  ✗ Error checking {name}: {e}")

                if found_elements:
                    print(
                        f"\n✓ Login verified! Found {len(found_elements)} post-login elements"
                    )
                    return True
                else:
                    print(
                        "\n⚠️  Warning: Could not verify login - no post-login elements found"
                    )

                    # Log page state for debugging
                    current_url = scraper.page.url
                    print(f"Login test - Current URL: {current_url}")

                    return False

            except Exception as e:
                print(f"\n✗ Error during verification: {e}")
                return False

    except GibneyScrapingError as e:
        print(f"\n✗ Scraping error: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_gibney_scrape_rentals(max_rentals=None):
    """Test full scraping functionality

    Args:
        max_rentals: Optional limit on number of rentals to scrape (for faster testing)
    """
    print("\n=== Testing Gibney Rental Scraping ===")
    if max_rentals:
        print(f"(Limited to {max_rentals} rentals for faster testing)")

    # Get credentials
    email = os.environ.get("TEST_GIBNEY_EMAIL")
    password = os.environ.get("TEST_GIBNEY_PASSWORD")

    if not email or not password:
        print("\n⚠️  No test credentials found!")
        print("Please provide credentials via backend/.env or environment variables")
        print("See test_gibney_login() for details.")
        return False

    print(f"Testing full scrape for: {email}")

    try:
        async with GibneyScraper(headless=True) as scraper:
            # Login
            print("Logging in...")
            start_time = datetime.now()
            await scraper.login(email, password)
            login_duration = (datetime.now() - start_time).total_seconds()
            print(f"✓ Login successful (took {login_duration:.2f} seconds)")

            # Scrape rentals
            print("\nScraping rentals...")
            scrape_start = datetime.now()
            rentals = await scraper.scrape_rentals(max_rentals=max_rentals)
            scrape_duration = (datetime.now() - scrape_start).total_seconds()

            print(f"\n✓ Scraping complete (took {scrape_duration:.2f} seconds)")
            print(f"Found {len(rentals)} rentals")

            # Display first few rentals
            if rentals:
                print("\nFirst 3 rentals:")
                for i, rental in enumerate(rentals[:3]):
                    print(f"\n{i+1}. {rental['name']}")
                    print(f"   Date: {rental['start_time']} - {rental['end_time']}")
                    print(f"   Studio: {rental['studio']}")
                    print(f"   Location: {rental['location']}")
                    print(f"   Status: {rental['status']}")
                    print(f"   Price: ${rental['price']:.2f}")

                if len(rentals) > 3:
                    print(f"\n... and {len(rentals) - 3} more rentals")
            else:
                print(
                    "\n⚠️  No rentals found - this might be normal if you have no bookings"
                )

            total_duration = (datetime.now() - start_time).total_seconds()
            print(f"\n✓ Total test duration: {total_duration:.2f} seconds")
            return True

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("Gibney Scraper End-to-End Tests")
    print("================================")
    print("\nNote: These tests connect to the real Gibney website.")
    print("Make sure you have valid credentials.\n")

    # Check for performance test mode
    if "--fast" in sys.argv or os.environ.get("FAST_TEST"):
        print("Running in FAST mode - limiting to 10 rentals\n")
        max_rentals = 10
    else:
        max_rentals = None
        print("Running full test (use --fast or FAST_TEST=1 for quicker test)\n")

    # Test login
    login_success = await test_gibney_login()

    if login_success:
        # If login works, test full scraping
        await asyncio.sleep(2)  # Brief pause between tests
        await test_gibney_scrape_rentals(max_rentals=max_rentals)
    else:
        print("\n✗ Skipping rental scraping test due to login failure")


if __name__ == "__main__":
    asyncio.run(main())
