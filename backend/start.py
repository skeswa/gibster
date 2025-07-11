#!/usr/bin/env python3
"""
Backend startup script for Docker container
"""

import os

import uvicorn
from dotenv import load_dotenv

# Load environment variables from backend/.env
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)


def main():
    """Main function to start the server"""
    # Get configuration from environment variables
    host = os.getenv("APP_HOST", "0.0.0.0")  # Use 0.0.0.0 for Docker
    port = int(os.getenv("APP_PORT", "8000"))
    reload = (
        os.getenv("APP_RELOAD", "false").lower() == "true"
    )  # Disable reload in Docker

    print(f"🚀 Starting Gibster server at http://{host}:{port}")
    print(f"📚 API documentation available at http://{host}:{port}/docs")

    # Add current directory to Python path so imports work
    import sys

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    # Import the app directly to avoid module path issues
    from main import app

    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
