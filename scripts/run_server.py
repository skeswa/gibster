#!/usr/bin/env python3
"""
Gibster FastAPI Server
Run with: python run_server.py
"""

import os
import sys

# Add parent directory to Python path to ensure backend module can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn
from dotenv import load_dotenv

# Load environment variables from backend/.env
backend_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"
)
env_path = os.path.join(backend_dir, ".env")
load_dotenv(dotenv_path=env_path)


def main():
    """Main function to start the server"""
    # Get configuration from environment variables
    host = os.getenv("APP_HOST", "127.0.0.1")
    port = int(os.getenv("APP_PORT", "8000"))
    reload = os.getenv("APP_RELOAD", "true").lower() == "true"

    print(f"🚀 Starting Gibster server at http://{host}:{port}")
    print(f"📚 API documentation available at http://{host}:{port}/docs")

    uvicorn.run(
        "backend.main:app",  # Use import string instead of app object for reload support
        host=host,
        port=port,
        reload=reload,  # Enable auto-reload for development
        log_level="info",
    )


if __name__ == "__main__":
    main()
