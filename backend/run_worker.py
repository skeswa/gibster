#!/usr/bin/env python3
"""
Celery worker startup script for Docker container
"""

import os
import signal
import sys

# Add backend directory to Python path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from celery import Celery

# Import worker module to ensure tasks are registered
import worker

# Global flag for graceful shutdown
shutdown_requested = False


def handle_sigterm(signum, frame):
    """Handle SIGTERM for graceful shutdown"""
    global shutdown_requested
    print(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_requested = True
    # Let Celery handle the shutdown gracefully
    if worker.celery_app:
        worker.celery_app.control.shutdown()


# Register signal handlers
signal.signal(signal.SIGTERM, handle_sigterm)
signal.signal(signal.SIGINT, handle_sigterm)

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
                "--without-heartbeat",  # Disable heartbeat in container environment
                "--without-gossip",  # Disable gossip in container environment
                "--without-mingle",  # Disable synchronization on startup
            ]
        )
    else:
        print("❌ Celery is not enabled or Redis is not available")
        print("Please check your environment configuration")
        sys.exit(1)
