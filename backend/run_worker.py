#!/usr/bin/env python3
"""
Celery worker startup script for Docker container
"""

import os
import sys

# Add backend directory to Python path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from celery import Celery

# Import worker module to ensure tasks are registered
import worker

if __name__ == "__main__":
    if worker.USE_CELERY and worker.celery_app:
        print("🚀 Starting Celery worker...")
        print(f"📡 Connected to Redis at {worker.REDIS_HOST}:{worker.REDIS_PORT}")

        # Start the Celery worker
        worker.celery_app.worker_main(
            [
                "worker",
                "--loglevel=info",
                "--concurrency=1",  # Single worker for now
                "--pool=solo",  # Use solo pool for simplicity in container
            ]
        )
    else:
        print("❌ Celery is not enabled or Redis is not available")
        print("Please check your environment configuration")
        sys.exit(1)
