# Sync Error Handling Documentation

This document describes how sync errors are handled in Gibster to ensure users always have visibility into sync failures.

## Overview

The sync process involves multiple stages where errors can occur:
1. Job creation and initialization
2. Database connection validation
3. Scraper initialization
4. Gibney website authentication
5. Booking data retrieval
6. Database updates

## Error Handling Implementation

### Early Error Detection

Previously, errors occurring before sync logger initialization would not be logged, causing the dashboard to show a "pending" status indefinitely. This has been fixed by:

1. **Immediate Job Creation with Error Handling**: The sync job creation is wrapped in a try-catch block that creates a failed job record if initialization fails.

2. **Sync Logger Initialization**: The sync logger is initialized immediately after job creation to capture all subsequent errors.

3. **Fallback Error Logging**: If the sync logger is not available, errors are still logged via the standard logger and the job status is updated.

### Error Categorization

Errors are categorized to provide user-friendly messages:

| Error Type | User Message |
|------------|--------------|
| Invalid credentials / Login failed | "Invalid Gibney credentials. Please update your login information." |
| Timeout errors | "Connection timed out. Gibney website may be slow or unavailable." |
| Network/connection errors | "Network error. Please check your internet connection." |
| Database errors | "Database error. Please try again later." |
| Browser/Playwright errors | "Browser automation error. Please contact support." |
| Decryption/InvalidToken errors | "Failed to decrypt Gibney credentials. Please update your login information." |
| Other errors | "Sync error: [original error message]" |

### Error Storage

1. **SyncJob Table**: 
   - `status`: Set to "failed"
   - `error_message`: User-friendly error message
   - `completed_at`: Timestamp when error occurred

2. **SyncJobLog Table**:
   - Detailed error logs with stack traces
   - Log level set to "ERROR"
   - Structured `details` field contains error type and traceback

### Frontend Error Display

The Dashboard component properly displays errors:
- Shows error messages in the sync status section
- Displays error alerts when sync fails
- Allows viewing detailed logs via the logs modal

## Common Error Scenarios

### 1. Database Connection Failure
- **When**: Database is unavailable or credentials are incorrect
- **Result**: Failed job created with appropriate error message
- **User sees**: "Database error. Please try again later."

### 2. Invalid Gibney Credentials
- **When**: User's Gibney login credentials are incorrect or expired
- **Result**: Job marked as failed with authentication error
- **User sees**: "Invalid Gibney credentials. Please update your login information."

### 3. Network Issues
- **When**: Internet connection problems or Gibney website is down
- **Result**: Job fails with network error details
- **User sees**: "Network error" or "Connection timed out" message

### 4. Browser Automation Errors
- **When**: Playwright browser initialization or navigation fails
- **Result**: Job fails with browser error details
- **User sees**: "Browser automation error. Please contact support."

### 5. Credential Decryption Errors
- **When**: Stored Gibney credentials cannot be decrypted (e.g., encryption key changed)
- **Result**: Job fails with InvalidToken error
- **User sees**: "Failed to decrypt Gibney credentials. Please update your login information."
- **Note**: Some cryptography exceptions have empty string representations, which is handled specially

## Troubleshooting

### Sync Stuck in "Pending" Status

This should no longer occur with the improved error handling. If it does:

1. Check the SyncJob table for jobs without a `completed_at` timestamp
2. Look for stale jobs (running > 10 minutes) - these are automatically marked as failed
3. Review application logs for unhandled exceptions

### No Logs for Failed Sync

If a sync fails without logs:

1. Check if the job record exists in the database
2. Verify the sync logger initialization succeeded
3. Check application logs for database connection issues

### Manual Recovery

If a sync job is truly stuck:

1. The stale job detection runs every 15 minutes and marks jobs running > 10 minutes as failed
2. Users can trigger a new sync which will check for existing running jobs
3. Admin endpoint `/api/v1/admin/cleanup-sync-jobs` can be used to clean up old jobs

## Code References

- Error handling logic: `backend/worker.py:93-293`
- Sync logger: `backend/sync_logger.py`
- Error categorization: `backend/worker.py:235-272`
- Frontend error display: `frontend/src/components/Dashboard.tsx:584-591`
- Test coverage: `backend/tests/test_sync_errors.py`