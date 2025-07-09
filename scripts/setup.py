#!/usr/bin/env python3
"""
Gibster Setup Script
Helps set up the development environment
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(command, description=""):
    """Run a shell command and handle errors"""
    print(f"{'='*50}")
    print(f"📦 {description}")
    print(f"Running: {command}")
    print(f"{'='*50}")

    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ Error: {description}")
        print(f"Command: {command}")
        print(f"Error: {result.stderr}")
        return False
    else:
        print(f"✅ Success: {description}")
        if result.stdout:
            print(result.stdout)
        return True


def setup_environment():
    """Set up the development environment"""
    print("🚀 Setting up Gibster development environment...")

    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False

    print(f"✅ Python {sys.version} detected")

    # Create .env file if it doesn't exist
    if not os.path.exists(".env"):
        print("📝 Creating .env file from .env.example...")
        if os.path.exists(".env.example"):
            import shutil

            shutil.copy(".env.example", ".env")
            print("✅ .env file created. Please edit it with your settings.")
        else:
            # Create a basic .env file
            env_content = """# Gibster Environment Configuration
DATABASE_URL=sqlite:///./gibster.db
SECRET_KEY=development-secret-key-change-in-production
ENCRYPTION_KEY=development-encryption-key-change-in-production
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Your Gibney credentials (for testing)
TEST_GIBNEY_EMAIL=your-email@example.com
TEST_GIBNEY_PASSWORD=your-password
"""
            with open(".env", "w") as f:
                f.write(env_content)
            print("✅ Basic .env file created. Please edit it with your settings.")

    # Install Python dependencies
    if not run_command(
        "pip install -r backend/requirements.txt", "Installing Python dependencies"
    ):
        return False

    # Install Playwright browsers
    if not run_command("playwright install chromium", "Installing Playwright browser"):
        return False

    print("\n🎉 Gibster setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit .env file with your configuration")
    print("2. Start Redis: redis-server")
    print("3. Start the API server: python run_server.py")
    print("4. Start the worker: python run_worker.py")
    print("5. Access the web UI: http://localhost:8000")
    print("\n📚 For more information, see README.md")

    return True


def setup_frontend():
    """Set up the React frontend"""
    frontend_dir = Path("frontend")

    if not frontend_dir.exists():
        print("❌ Frontend directory not found")
        return False

    os.chdir(frontend_dir)

    print("📦 Setting up React frontend...")

    # Install Node.js dependencies
    if not run_command("npm install", "Installing Node.js dependencies"):
        return False

    print("✅ Frontend setup completed!")
    print("To start the frontend: cd frontend && npm start")

    return True


def main():
    """Main setup function"""
    if len(sys.argv) > 1 and sys.argv[1] == "frontend":
        setup_frontend()
    else:
        setup_environment()


if __name__ == "__main__":
    main()
