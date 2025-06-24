#!/usr/bin/env python3
"""
Gibster FastAPI Server
Run with: python run_server.py
"""

import uvicorn
from app.main import app

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload for development
        log_level="info"
    ) 