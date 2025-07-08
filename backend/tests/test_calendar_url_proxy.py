"""Test calendar URL generation with frontend proxy support"""
import os
import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from ..calendar_generator import get_user_calendar
from ..main import app, get_current_user
from ..models import User


class TestCalendarUrlGeneration:
    """Test calendar URL generation with frontend proxy support"""

    @pytest.fixture
    def mock_user(self):
        """Create a mock user for testing"""
        user = MagicMock(spec=User)
        user.id = uuid.uuid4()
        user.email = "test@example.com"
        user.calendar_uuid = uuid.uuid4()
        return user

    @pytest.fixture 
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_calendar_url_without_frontend_base_url(self, client, mock_user):
        """Test calendar URL generation falls back to request base URL"""
        # Mock the authentication
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        try:
            # Ensure FRONTEND_BASE_URL is not set
            with patch.dict(os.environ, {}, clear=True):
                response = client.get("/api/v1/user/calendar_url")
                
            assert response.status_code == 200
            data = response.json()
            
            # Should use the test client base URL
            expected_url = f"http://testserver/calendar/{mock_user.calendar_uuid}.ics"
            assert data["calendar_url"] == expected_url
            assert data["calendar_uuid"] == str(mock_user.calendar_uuid)
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()

    def test_calendar_url_with_frontend_base_url(self, client, mock_user):
        """Test calendar URL generation uses FRONTEND_BASE_URL when set"""
        # Mock the authentication
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        try:
            # Set FRONTEND_BASE_URL
            frontend_url = "https://app.gibster.com"
            with patch.dict(os.environ, {"FRONTEND_BASE_URL": frontend_url}):
                response = client.get("/api/v1/user/calendar_url")
                
            assert response.status_code == 200
            data = response.json()
            
            # Should use the frontend URL
            expected_url = f"{frontend_url}/calendar/{mock_user.calendar_uuid}.ics"
            assert data["calendar_url"] == expected_url
            assert data["calendar_uuid"] == str(mock_user.calendar_uuid)
        finally:
            app.dependency_overrides.clear()

    def test_calendar_url_with_trailing_slash(self, client, mock_user):
        """Test calendar URL generation handles trailing slashes correctly"""
        # Mock the authentication
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        try:
            # Set FRONTEND_BASE_URL with trailing slash
            frontend_url = "https://app.gibster.com/"
            with patch.dict(os.environ, {"FRONTEND_BASE_URL": frontend_url}):
                response = client.get("/api/v1/user/calendar_url")
                
            assert response.status_code == 200
            data = response.json()
            
            # Should strip the trailing slash
            expected_url = f"https://app.gibster.com/calendar/{mock_user.calendar_uuid}.ics"
            assert data["calendar_url"] == expected_url
        finally:
            app.dependency_overrides.clear()

    def test_calendar_url_different_protocols(self, client, mock_user):
        """Test calendar URL generation with different protocols"""
        # Mock the authentication
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        try:
            # Test with HTTP
            with patch.dict(os.environ, {"FRONTEND_BASE_URL": "http://localhost:3000"}):
                response = client.get("/api/v1/user/calendar_url")
                assert response.status_code == 200
                data = response.json()
                assert data["calendar_url"].startswith("http://localhost:3000/calendar/")
            
            # Test with HTTPS
            with patch.dict(os.environ, {"FRONTEND_BASE_URL": "https://secure.gibster.com"}):
                response = client.get("/api/v1/user/calendar_url")
                assert response.status_code == 200
                data = response.json()
                assert data["calendar_url"].startswith("https://secure.gibster.com/calendar/")
        finally:
            app.dependency_overrides.clear()

    # @pytest.mark.integration
    # def test_calendar_feed_endpoint_accessibility(self, client, mock_user):
    #     """Test that the calendar feed endpoint is accessible"""
    #     # Create a test request to the calendar endpoint
    #     # This tests that the endpoint exists and responds
    #     # Mock at the location where it's used in main.py
    #     with patch("backend.main.get_user_calendar", return_value="BEGIN:VCALENDAR\nEND:VCALENDAR") as mock_cal:
    #         response = client.get(f"/calendar/{mock_user.calendar_uuid}.ics")
    #         
    #     assert response.status_code == 200
    #     assert response.headers["content-type"] == "text/calendar"
    #     assert "gibney-bookings" in response.headers.get("content-disposition", "").lower()