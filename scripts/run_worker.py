#!/usr/bin/env python3
"""
Gibster Celery Worker
Run with: python run_worker.py
"""

import os
import sys

# Add parent directory to Python path to ensure backend module can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.worker import celery_app

if __name__ == "__main__":
    # Run the celery worker
    sys.argv = [
        "celery",
        "worker",
        "-A",
        "app.worker:celery_app",
        "--loglevel=info",
        "--concurrency=2",
    ]

    celery_app.worker_main()
