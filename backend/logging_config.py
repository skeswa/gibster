import logging
import logging.config
import os
import sys
from datetime import datetime
from typing import Any, Dict

from dotenv import load_dotenv

load_dotenv()


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging with additional context"""

    def format(self, record: logging.LogRecord) -> str:
        # Add timestamp
        record.timestamp = datetime.utcnow().isoformat()

        # Add service info
        record.service = "gibster-backend"
        record.version = "1.0.0"

        # Add environment
        record.environment = os.getenv("ENVIRONMENT", "development")

        # Format the message
        formatted = super().format(record)

        return formatted


def setup_logging() -> None:
    """Configure application logging"""

    # Get log level from environment
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    # Get environment
    environment = os.getenv("ENVIRONMENT", "development")

    # Configure logging based on environment
    if environment == "production":
        # Production: JSON structured logging
        log_format = (
            '{"timestamp": "%(timestamp)s", "service": "%(service)s", '
            '"version": "%(version)s", "environment": "%(environment)s", '
            '"level": "%(levelname)s", "logger": "%(name)s", '
            '"message": "%(message)s", "module": "%(module)s", '
            '"function": "%(funcName)s", "line": %(lineno)d}'
        )
    else:
        # Development: Human-readable format
        log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"

    # Logging configuration
    config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "structured": {
                "()": StructuredFormatter,
                "format": log_format,
                "datefmt": "%Y-%m-%d %H:%M:%S",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "structured",
                "stream": sys.stdout,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "structured",
                "filename": "logs/gibster.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            },
        },
        "loggers": {
            "": {  # Root logger
                "level": log_level,
                "handlers": (
                    ["console", "file"] if environment == "production" else ["console"]
                ),
                "propagate": False,
            },
            "gibster": {
                "level": log_level,
                "handlers": (
                    ["console", "file"] if environment == "production" else ["console"]
                ),
                "propagate": False,
            },
            "uvicorn": {"level": "INFO", "handlers": ["console"], "propagate": False},
            "sqlalchemy.engine": {
                "level": "WARNING",  # Reduce SQL query noise unless debugging
                "handlers": ["console"],
                "propagate": False,
            },
        },
    }

    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)

    # Apply configuration
    logging.config.dictConfig(config)

    # Log startup message
    logger = logging.getLogger("gibster.startup")
    logger.info(
        f"Logging configured for environment: {environment}, level: {log_level}"
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the gibster prefix"""
    return logging.getLogger(f"gibster.{name}")


# Request ID context (for tracking requests across logs)
import contextvars

request_id_context: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default=""
)


def set_request_id(request_id: str) -> None:
    """Set request ID for current context"""
    request_id_context.set(request_id)


def get_request_id() -> str:
    """Get request ID from current context"""
    return request_id_context.get("")


class RequestContextFilter(logging.Filter):
    """Add request ID to log records"""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True


# Add the filter to all handlers
def add_request_context_filter():
    """Add request context filter to all handlers"""
    for handler in logging.getLogger().handlers:
        handler.addFilter(RequestContextFilter())
