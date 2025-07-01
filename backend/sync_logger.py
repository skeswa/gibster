"""
Sync Job Logging Helper

This module provides utilities for logging sync job activities to the database.
It captures detailed information about each step of the sync process for debugging
and monitoring purposes.
"""

import traceback
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from .logging_config import get_logger
from .models import SyncJobLog

logger = get_logger("sync_logger")


class SyncJobLogger:
    """Helper class for logging sync job activities to the database"""

    def __init__(self, db: Session, sync_job_id: UUID):
        self.db = db
        self.sync_job_id = sync_job_id
        self._start_time = datetime.now(timezone.utc)

    def _create_log_entry(
        self, level: str, message: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Create a log entry in the database"""
        try:
            log_entry = SyncJobLog(
                sync_job_id=self.sync_job_id,
                timestamp=datetime.now(timezone.utc),
                level=level,
                message=message,
                details=details or {},
            )
            self.db.add(log_entry)
            self.db.commit()
            
            # Also log to file/console
            log_message = f"[SyncJob {self.sync_job_id}] {message}"
            if level == "DEBUG":
                logger.debug(log_message)
            elif level == "INFO":
                logger.info(log_message)
            elif level == "WARNING":
                logger.warning(log_message)
            elif level == "ERROR":
                logger.error(log_message)
                
        except Exception as e:
            # Don't let logging errors break the sync
            logger.error(f"Failed to create sync job log entry: {e}")
            self.db.rollback()

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log a debug message"""
        self._create_log_entry("DEBUG", message, kwargs if kwargs else None)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log an info message"""
        self._create_log_entry("INFO", message, kwargs if kwargs else None)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log a warning message"""
        self._create_log_entry("WARNING", message, kwargs if kwargs else None)

    def error(self, message: str, error: Optional[Exception] = None, **kwargs: Any) -> None:
        """Log an error message with optional exception details"""
        details = kwargs.copy() if kwargs else {}
        
        if error:
            details.update({
                "error_type": type(error).__name__,
                "error_message": str(error),
                "traceback": traceback.format_exc(),
            })
            
        self._create_log_entry("ERROR", message, details)

    def log_timing(self, operation: str, start_time: datetime, **kwargs: Any) -> None:
        """Log timing information for an operation"""
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        details = kwargs.copy() if kwargs else {}
        details["duration_seconds"] = duration
        
        self._create_log_entry(
            "INFO",
            f"{operation} completed in {duration:.2f} seconds",
            details
        )

    def log_scraper_event(
        self,
        event_type: str,
        message: str,
        url: Optional[str] = None,
        selector: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        """Log scraper-specific events with structured data"""
        details = {
            "event_type": event_type,
            "url": url,
            "selector": selector,
            **kwargs
        }
        
        # Remove None values
        details = {k: v for k, v in details.items() if v is not None}
        
        self._create_log_entry("INFO", message, details)

    def log_booking_processed(
        self,
        booking_id: str,
        booking_name: str,
        action: str,  # 'created', 'updated', 'unchanged'
        **kwargs: Any
    ) -> None:
        """Log individual booking processing"""
        details = {
            "booking_id": booking_id,
            "booking_name": booking_name,
            "action": action,
            **kwargs
        }
        
        self._create_log_entry(
            "INFO",
            f"Booking {booking_name} {action}",
            details
        )

    def log_sync_summary(
        self,
        total_bookings: int,
        created: int,
        updated: int,
        unchanged: int,
        errors: int = 0
    ) -> None:
        """Log a summary of the sync operation"""
        total_duration = (datetime.now(timezone.utc) - self._start_time).total_seconds()
        
        details = {
            "total_bookings": total_bookings,
            "created": created,
            "updated": updated,
            "unchanged": unchanged,
            "errors": errors,
            "duration_seconds": total_duration,
        }
        
        self._create_log_entry(
            "INFO",
            f"Sync completed: {total_bookings} bookings processed in {total_duration:.2f} seconds",
            details
        )