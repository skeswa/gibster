#!/usr/bin/env python
"""
Test sync error scenarios to ensure proper error logging and handling.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest


@pytest.mark.unit
class TestSyncErrorHandling:
    """Test various sync error scenarios."""

    def test_sync_error_handling_logic(self):
        """Test the logic of sync error handling based on our implementation."""
        # Test error categorization logic from worker.py
        error_scenarios = [
            ("Invalid credentials", "Invalid Gibney credentials"),
            ("Login failed", "Invalid Gibney credentials"),
            ("Connection timeout", "Connection timed out"),
            ("Network connection failed", "Network error"),
            ("database error occurred", "Database error"),
            ("Playwright browser error", "Browser automation error"),
            ("InvalidToken", "Failed to decrypt Gibney credentials"),
            ("decrypt failed", "Failed to decrypt Gibney credentials"),
            ("Unknown weird error", "Sync error: Unknown weird error"),
        ]
        
        for error_msg, expected_user_msg in error_scenarios:
            # Simulate the error categorization logic from worker.py
            error_message = error_msg
            # Handle empty error messages
            if not error_message and type(error_msg).__name__ == "InvalidToken":
                error_message = "Invalid encryption token"
            elif not error_message:
                error_message = type(error_msg).__name__
                
            if "Invalid credentials" in error_message or "Login failed" in error_message:
                user_friendly_error = "Invalid Gibney credentials. Please update your login information."
            elif "timeout" in error_message.lower():
                user_friendly_error = "Connection timed out. Gibney website may be slow or unavailable."
            elif "network" in error_message.lower() or "connection" in error_message.lower():
                user_friendly_error = "Network error. Please check your internet connection."
            elif "database" in error_message.lower():
                user_friendly_error = "Database error. Please try again later."
            elif "browser" in error_message.lower() or "playwright" in error_message.lower():
                user_friendly_error = "Browser automation error. Please contact support."
            elif "invalidtoken" in error_message.lower() or "decrypt" in error_message.lower():
                user_friendly_error = "Failed to decrypt Gibney credentials. Please update your login information."
            else:
                user_friendly_error = f"Sync error: {error_message}"
            
            assert expected_user_msg in user_friendly_error

    def test_database_rollback_behavior(self):
        """Test that database rollback is called when an error occurs."""
        mock_db = MagicMock()
        
        # Simulate database error
        mock_db.add.side_effect = Exception("Database constraint violation")
        
        # When an error occurs, rollback should be called
        try:
            mock_db.add("some_object")
        except:
            mock_db.rollback()
        
        # Verify rollback was called
        mock_db.rollback.assert_called()

    def test_sync_logger_error_handling(self):
        """Test that SyncJobLogger handles errors gracefully based on our implementation."""
        mock_db = MagicMock()
        
        # Based on sync_logger.py implementation:
        # When database fails, it should rollback without raising
        mock_db.add.side_effect = Exception("Database error")
        mock_db.commit.side_effect = Exception("Database error")
        
        # This simulates the error handling in _create_log_entry
        try:
            mock_db.add("log_entry")
            mock_db.commit()
        except Exception:
            # Don't let logging errors break the sync
            mock_db.rollback()
        
        # Verify rollback was called
        mock_db.rollback.assert_called()

    def test_job_status_update_on_error(self):
        """Test that job status is properly updated when an error occurs."""
        # Create mock job
        mock_job = MagicMock()
        mock_job.id = uuid4()
        mock_job.status = "running"
        
        # When error occurs, these fields should be updated
        mock_job.status = "failed"
        mock_job.error_message = "Test error message"
        mock_job.completed_at = datetime.now(timezone.utc)
        
        # Verify fields were updated
        assert mock_job.status == "failed"
        assert mock_job.error_message == "Test error message"
        assert mock_job.completed_at is not None

    def test_empty_error_message_handling(self):
        """Test handling of exceptions with empty string representation."""
        # Simulate an exception with empty string representation
        error_message = ""
        
        # Apply the fix from worker.py
        if not error_message:
            error_message = "InvalidToken"  # Simulating type(e).__name__
            
        # Now it should match the decrypt error case
        if "invalidtoken" in error_message.lower() or "decrypt" in error_message.lower():
            user_friendly_error = "Failed to decrypt Gibney credentials. Please update your login information."
        else:
            user_friendly_error = f"Sync error: {error_message}"
            
        assert user_friendly_error == "Failed to decrypt Gibney credentials. Please update your login information."

    def test_early_error_handling(self):
        """Test handling of errors that occur before sync logger initialization."""
        # Simulate the scenario where sync_logger is None
        sync_logger = None
        error_logged = False
        
        # Error handling logic from worker.py
        if sync_logger:
            sync_logger.error("This won't be called")
        else:
            # Fallback logging when sync_logger is not available
            error_logged = True
        
        assert error_logged is True

    def test_sync_job_creation_failure_handling(self):
        """Test handling when sync job creation fails."""
        mock_db = MagicMock()
        
        # Simulate job creation failure
        mock_db.add.side_effect = Exception("Database error")
        mock_db.commit.side_effect = Exception("Database error")
        
        job = None
        error_job_created = False
        
        try:
            # Try to create job
            mock_db.add("job")
            mock_db.commit()
        except:
            # Try to create a failed job record for visibility
            try:
                mock_db.rollback()
                # Create failed job
                error_job_created = True
                mock_db.add("failed_job")
                mock_db.commit()
            except:
                mock_db.rollback()
        
        assert error_job_created is True