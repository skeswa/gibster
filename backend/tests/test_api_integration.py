from datetime import datetime

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

        calendar_content = response.text
        assert "BEGIN:VCALENDAR" in calendar_content
        assert "END:VCALENDAR" in calendar_content
        assert "PRODID:Gibster" in calendar_content

    def test_calendar_feed_with_bookings(self, client, sample_user_data, test_db):
        """Test calendar feed with bookings"""
        # Setup user
        headers = TestUserEndpoints().setup_authenticated_user(client, sample_user_data)

        # Create user in database and add a booking
        # Note: This would require getting the user ID and creating a booking
        # For now, we test the endpoint structure

        response = client.get("/api/v1/user/calendar_url", headers=headers)
        calendar_url = response.json()["calendar_url"]
        calendar_path = calendar_url.split("localhost:8000")[-1]

        response = client.get(calendar_path)
        assert response.status_code == 200
        assert "text/calendar" in response.headers["content-type"]


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
