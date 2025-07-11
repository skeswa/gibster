#!/usr/bin/env python3
"""
Health check script for Celery worker in Kubernetes
"""

import os
import sys

from celery import Celery
from celery.exceptions import TimeoutError

# Configure Redis connection
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

# Build Redis URL
if REDIS_PASSWORD:
    REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0"
else:
    REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"

try:
    # Create a minimal Celery app instance for health checking
    app = Celery("gibster_health", broker=REDIS_URL)

    # Try to inspect active workers
    inspect = app.control.inspect(timeout=5)
    active_workers = inspect.active()

    if active_workers:
        # At least one worker is active
        print("Celery worker is healthy")
        sys.exit(0)
    else:
        # No active workers found
        print("No active Celery workers found")
        sys.exit(1)

except TimeoutError:
    print("Timeout connecting to Celery workers")
    sys.exit(1)
except Exception as e:
    print(f"Health check failed: {e}")
    sys.exit(1)
