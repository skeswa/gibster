from datetime import datetime, timezone

import pytest

from models import Booking, User


@pytest.mark.integration
class TestAuthenticationEndpoints:
    """Test authentication API endpoints"""

    def test_register_user_success(self, client, sample_user_data):
        """Test successful user registration"""
        response = client.post("/api/v1/auth/register", json=sample_user_data)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == sample_user_data["email"]
        assert "id" in data
        assert "calendar_uuid" in data
        assert "password" not in data  # Password should not be returned

    def test_register_user_duplicate_email(self, client, sample_user_data):
        """Test registration with duplicate email"""
        # Register first user
        client.post("/api/v1/auth/register", json=sample_user_data)

        # Try to register with same email
        response = client.post("/api/v1/auth/register", json=sample_user_data)

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_user_invalid_email(self, client):
        """Test registration with invalid email"""
        invalid_data = {"email": "invalid-email", "password": "password123"}
        response = client.post("/api/v1/auth/register", json=invalid_data)

        assert response.status_code == 422  # Validation error

    def test_login_success(self, client, sample_user_data):
        """Test successful login"""
        # First register user
        client.post("/api/v1/auth/register", json=sample_user_data)

        # Then login
        login_data = {
            "username": sample_user_data["email"],
            "password": sample_user_data["password"],
        }
        response = client.post("/api/v1/auth/token", data=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self, client, sample_user_data):
        """Test login with invalid credentials"""
        login_data = {
            "username": sample_user_data["email"],
            "password": "wrongpassword",
        }
        response = client.post("/api/v1/auth/token", data=login_data)

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()


@pytest.mark.integration
class TestUserEndpoints:
    """Test user management API endpoints"""

    def setup_authenticated_user(self, client, sample_user_data):
        """Helper to create and authenticate a user"""
        # Register user
        client.post("/api/v1/auth/register", json=sample_user_data)

        # Login to get token
        login_data = {
            "username": sample_user_data["email"],
            "password": sample_user_data["password"],
        }
        response = client.post("/api/v1/auth/token", data=login_data)
        token = response.json()["access_token"]

        return {"Authorization": f"Bearer {token}"}

    def test_update_credentials_success(
        self, client, sample_user_data, sample_credentials
    ):
        """Test successful credential update"""
        headers = self.setup_authenticated_user(client, sample_user_data)

        response = client.put(
            "/api/v1/user/credentials", json=sample_credentials, headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Credentials updated successfully"

    def test_update_credentials_unauthenticated(self, client, sample_credentials):
        """Test credential update without authentication"""
        response = client.put("/api/v1/user/credentials", json=sample_credentials)

        assert response.status_code == 401

    def test_get_calendar_url(self, client, sample_user_data):
        """Test getting calendar URL"""
        headers = self.setup_authenticated_user(client, sample_user_data)

        response = client.get("/api/v1/user/calendar_url", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "calendar_url" in data
        assert "calendar/" in data["calendar_url"]
        assert ".ics" in data["calendar_url"]

    def test_get_bookings_empty(self, client, sample_user_data):
        """Test getting bookings when user has none"""
        headers = self.setup_authenticated_user(client, sample_user_data)

        response = client.get("/api/v1/user/bookings", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_sync_bookings_no_credentials(self, client, sample_user_data):
        """Test sync without Gibney credentials"""
        headers = self.setup_authenticated_user(client, sample_user_data)

        response = client.post("/api/v1/user/sync", headers=headers)

        assert response.status_code == 400
        assert "credentials" in response.json()["detail"].lower()

    def test_sync_bookings_with_credentials(
        self, client, sample_user_data, sample_credentials
    ):
        """Test sync with Gibney credentials (will fail without real login)"""
        headers = self.setup_authenticated_user(client, sample_user_data)

        # Add credentials first
        client.put("/api/v1/user/credentials", json=sample_credentials, headers=headers)

        response = client.post("/api/v1/user/sync", headers=headers)

        # This will likely fail since we don't have real Gibney credentials
        # but we test that the endpoint is reachable and handles the request
        assert response.status_code in [200, 400, 500]  # Various expected responses


@pytest.mark.integration
class TestCalendarEndpoints:
    """Test calendar feed endpoints"""

    def test_calendar_feed_invalid_uuid(self, client):
        """Test calendar feed with invalid UUID"""
        response = client.get("/calendar/invalid-uuid.ics")

        assert response.status_code == 404

    def test_calendar_feed_malformed_uuid(self, client):
        """Test calendar feed with malformed UUID format"""
        response = client.get("/calendar/not-a-uuid.ics")
        assert response.status_code == 404

        response = client.get("/calendar/12345.ics")
        assert response.status_code == 404

    def test_calendar_feed_valid_uuid_no_bookings(
        self, client, sample_user_data, test_db
    ):
        """Test calendar feed with valid UUID but no bookings"""
        # Setup user first
        headers = TestUserEndpoints().setup_authenticated_user(client, sample_user_data)

        # Get calendar URL
        response = client.get("/api/v1/user/calendar_url", headers=headers)
        calendar_url = response.json()["calendar_url"]

        # Extract the path from the URL
        calendar_path = calendar_url.split("localhost:8000")[-1]

        # Get calendar feed
        response = client.get(calendar_path)

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/calendar; charset=utf-8"

        # Check personalized headers
        assert "content-disposition" in response.headers
        content_disposition = response.headers["content-disposition"]
        expected_filename = (
            f"gibster-{sample_user_data['email'].replace('@', '-at-')}.ics"
        )
        assert expected_filename in content_disposition
        assert "inline" in content_disposition

        # Check cache headers
        assert response.headers["cache-control"] == "public, max-age=7200"

        # Note: X-WR-CALNAME is part of the calendar content, not HTTP headers
        calendar_content = response.text
        assert "BEGIN:VCALENDAR" in calendar_content
        assert "END:VCALENDAR" in calendar_content
        assert "PRODID:Gibster" in calendar_content
        assert f"X-WR-CALNAME:Gibster - {sample_user_data['email']}" in calendar_content
        assert (
            "X-WR-CALDESC:Your Gibney dance studio bookings synced by Gibster"
            in calendar_content
        )

    def test_calendar_feed_with_bookings(self, client, sample_user_data, test_db):
        """Test calendar feed with bookings"""
        # Setup user
        headers = TestUserEndpoints().setup_authenticated_user(client, sample_user_data)

        # Get the user from the database to add bookings
        user = (
            test_db.query(User).filter(User.email == sample_user_data["email"]).first()
        )

        # Create test bookings
        booking1 = Booking(
            id="test-booking-1",
            user_id=user.id,
            name="R-123456",
            start_time=datetime(2024, 3, 15, 10, 0),
            end_time=datetime(2024, 3, 15, 12, 0),
            studio="Studio A",
            location="280 Broadway",
            status="Confirmed",
            price=75.00,
            record_url="https://gibney.my.site.com/s/rental-form?Id=test-booking-1",
            last_seen=datetime.now(timezone.utc),
        )

        booking2 = Booking(
            id="test-booking-2",
            user_id=user.id,
            name="R-789012",
            start_time=datetime(2024, 3, 20, 14, 0),
            end_time=datetime(2024, 3, 20, 16, 0),
            studio="Studio B",
            location="890 Broadway",
            status="Confirmed",
            price=100.00,
            record_url="https://gibney.my.site.com/s/rental-form?Id=test-booking-2",
            last_seen=datetime.now(timezone.utc),
        )

        test_db.add(booking1)
        test_db.add(booking2)
        test_db.commit()

        # Get calendar URL and fetch the calendar
        response = client.get("/api/v1/user/calendar_url", headers=headers)
        calendar_url = response.json()["calendar_url"]
        calendar_path = calendar_url.split("localhost:8000")[-1]

        response = client.get(calendar_path)
        assert response.status_code == 200
        assert "text/calendar" in response.headers["content-type"]

        # Check personalized filename
        content_disposition = response.headers["content-disposition"]
        expected_filename = (
            f"gibster-{sample_user_data['email'].replace('@', '-at-')}.ics"
        )
        assert expected_filename in content_disposition

        # Check calendar content includes bookings
        calendar_content = response.text
        assert "BEGIN:VEVENT" in calendar_content
        assert "Studio A at 280 Broadway" in calendar_content
        assert "Studio B at 890 Broadway" in calendar_content
        assert "R-123456" in calendar_content
        assert "R-789012" in calendar_content
        assert f"X-WR-CALNAME:Gibster - {sample_user_data['email']}" in calendar_content

    def test_calendar_feed_special_email_characters(self, client, test_db):
        """Test calendar feed with emails containing special characters"""
        # Test with email containing special characters
        special_email_data = {
            "email": "test+special.user@example.com",
            "password": "testpassword123",
        }

        headers = TestUserEndpoints().setup_authenticated_user(
            client, special_email_data
        )

        # Get calendar URL
        response = client.get("/api/v1/user/calendar_url", headers=headers)
        calendar_url = response.json()["calendar_url"]
        calendar_path = calendar_url.split("localhost:8000")[-1]

        # Get calendar feed
        response = client.get(calendar_path)
        assert response.status_code == 200

        # Check filename formatting
        content_disposition = response.headers["content-disposition"]
        expected_filename = "gibster-test+special.user-at-example.com.ics"
        assert expected_filename in content_disposition

        # Check calendar name in content
        calendar_content = response.text
        assert (
            "X-WR-CALNAME:Gibster - test+special.user@example.com" in calendar_content
        )

    def test_calendar_headers_caching_validation(
        self, client, sample_user_data, test_db
    ):
        """Test that calendar responses have proper caching headers"""
        headers = TestUserEndpoints().setup_authenticated_user(client, sample_user_data)

        response = client.get("/api/v1/user/calendar_url", headers=headers)
        calendar_url = response.json()["calendar_url"]
        calendar_path = calendar_url.split("localhost:8000")[-1]

        response = client.get(calendar_path)

        # Verify caching headers
        assert response.headers["cache-control"] == "public, max-age=7200"
        assert response.headers["access-control-allow-origin"] == "*"

        # Verify the X-WR-CALNAME is NOT in HTTP headers (only in content)
        assert "x-wr-calname" not in response.headers


@pytest.mark.integration
class TestAPIValidation:
    """Test API input validation"""

    def test_register_missing_fields(self, client):
        """Test registration with missing required fields"""
        # Missing password
        response = client.post(
            "/api/v1/auth/register", json={"email": "test@example.com"}
        )
        assert response.status_code == 422

        # Missing email
        response = client.post(
            "/api/v1/auth/register", json={"password": "password123"}
        )
        assert response.status_code == 422

        # Empty JSON
        response = client.post("/api/v1/auth/register", json={})
        assert response.status_code == 422

    def test_credentials_validation(self, client, sample_user_data):
        """Test credentials endpoint validation"""
        headers = TestUserEndpoints().setup_authenticated_user(client, sample_user_data)

        # Missing gibney_email
        response = client.put(
            "/api/v1/user/credentials",
            json={"gibney_password": "pass"},
            headers=headers,
        )
        assert response.status_code == 422

        # Missing gibney_password
        response = client.put(
            "/api/v1/user/credentials",
            json={"gibney_email": "email@example.com"},
            headers=headers,
        )
        assert response.status_code == 422

    def test_invalid_bearer_token(self, client):
        """Test endpoints with invalid bearer token"""
        headers = {"Authorization": "Bearer invalid-token"}

        endpoints = [
            "/api/v1/user/credentials",
            "/api/v1/user/calendar_url",
            "/api/v1/user/bookings",
            "/api/v1/user/sync",
        ]

        for endpoint in endpoints:
            if endpoint == "/api/v1/user/credentials":
                response = client.put(
                    endpoint,
                    json={"gibney_email": "test", "gibney_password": "test"},
                    headers=headers,
                )
            elif endpoint == "/api/v1/user/sync":
                response = client.post(endpoint, headers=headers)
            else:
                response = client.get(endpoint, headers=headers)

            assert response.status_code == 401


@pytest.mark.integration
class TestErrorHandling:
    """Test API error handling"""

    def test_404_endpoints(self, client):
        """Test that non-existent endpoints return 404"""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404

        response = client.post("/api/v1/nonexistent")
        assert response.status_code == 404

    def test_method_not_allowed(self, client):
        """Test that wrong HTTP methods return 405"""
        # These endpoints should only accept specific methods
        response = client.get("/api/v1/auth/register")  # Should be POST
        assert response.status_code == 405

        response = client.delete("/api/v1/auth/token")  # Should be POST
        assert response.status_code == 405
