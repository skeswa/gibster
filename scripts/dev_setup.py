#!/usr/bin/env python3
"""
Gibster Development Setup Script

This script sets up the local development environment without Docker.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(
            command, shell=True, check=True, capture_output=True, text=True
        )
        print(f"✅ {description} completed successfully")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return None


def check_python_version():
    """Check if Python version is 3.8+"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)

    print(f"✅ Python {sys.version.split()[0]} detected")


def check_node_version():
    """Check if Node.js is installed and version is 14+"""
    try:
        result = subprocess.run(
            "node --version", shell=True, check=True, capture_output=True, text=True
        )
        version_str = result.stdout.strip()
        print(f"✅ Node.js {version_str} detected")

        # Extract major version number
        major_version = int(
            version_str[1:].split(".")[0]
        )  # Remove 'v' prefix and get major version
        if major_version < 14:
            print("⚠️  Node.js 14 or higher is recommended for optimal compatibility")

        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(
            "❌ Node.js not found. Please install Node.js 14+ from https://nodejs.org/"
        )
        return False


def setup_virtual_environment():
    """Create and activate virtual environment"""
    venv_path = Path("venv")

    if venv_path.exists():
        print("✅ Virtual environment already exists")
        return

    run_command(f"{sys.executable} -m venv venv", "Creating virtual environment")


def install_dependencies():
    """Install Python dependencies"""
    # Determine the correct pip path
    if os.name == "nt":  # Windows
        pip_path = "venv\\Scripts\\pip"
        python_path = "venv\\Scripts\\python"
    else:  # Unix/Linux/macOS
        pip_path = "venv/bin/pip"
        python_path = "venv/bin/python"

    # Upgrade pip first
    run_command(f"{python_path} -m pip install --upgrade pip", "Upgrading pip")

    # Install requirements
    run_command(
        f"{pip_path} install -r requirements.txt", "Installing Python dependencies"
    )

    # Install Playwright browsers
    run_command(
        f"{python_path} -m playwright install chromium",
        "Installing Playwright Chromium browser",
    )


def install_frontend_dependencies():
    """Install frontend dependencies"""
    frontend_path = Path("frontend")
    if not frontend_path.exists():
        print("⚠️  Frontend directory not found, skipping frontend setup")
        return False

    # Change to frontend directory
    original_cwd = os.getcwd()
    os.chdir(frontend_path)

    try:
        # Install npm dependencies
        result = run_command("npm install", "Installing frontend dependencies")
        if result is None:
            print("❌ Failed to install frontend dependencies")
            return False

        print("✅ Frontend dependencies installed successfully")
        return True
    finally:
        # Change back to original directory
        os.chdir(original_cwd)


def create_env_file():
    """Create .env file from .env.example if it doesn't exist"""
    env_file = Path(".env")
    env_example = Path(".env.example")

    if not env_file.exists():
        if env_example.exists():
            import shutil

            shutil.copy(env_example, env_file)
            print("✅ Created .env file from .env.example")
        else:
            # Fallback if .env.example doesn't exist
            env_content = """# Gibster Local Development Configuration
# Copy from .env.example and customize

GIBNEY_EMAIL=your-email@example.com
GIBNEY_PASSWORD=your-password
SECRET_KEY=development-secret-key-change-in-production
ENCRYPTION_KEY=development-encryption-key-change-in-production
USE_CELERY=false
DATABASE_DEBUG=false
APP_HOST=127.0.0.1
APP_PORT=8000
APP_RELOAD=true
"""
            with open(env_file, "w") as f:
                f.write(env_content)
            print("✅ Created .env file with basic configuration")

        print("⚠️  IMPORTANT: Edit .env file and set your actual Gibney credentials")
        print("   Also generate secure SECRET_KEY and ENCRYPTION_KEY for production")
    else:
        print("✅ .env file already exists")


def initialize_database():
    """Initialize the SQLite database"""
    # Determine the correct Python path
    if os.name == "nt":  # Windows
        python_path = "venv\\Scripts\\python"
    else:  # Unix/Linux/macOS
        python_path = "venv/bin/python"

    run_command(
        f"{python_path} -c \"from app.database import engine; from app.models import Base; Base.metadata.create_all(bind=engine); print('Database tables created')\"",
        "Initializing SQLite database",
    )


def check_optional_services():
    """Check for optional services like Redis"""
    print("\n🔍 Checking optional services:")

    # Check Redis
    redis_result = run_command("redis-cli ping", "Testing Redis connection")
    if redis_result and "PONG" in redis_result.stdout:
        print("✅ Redis is available - you can enable USE_CELERY=true in .env")
    else:
        print("ℹ️  Redis not available - background tasks will run synchronously")


def print_next_steps(frontend_setup_success):
    """Print instructions for next steps"""
    print("\n🎉 Development environment setup complete!")
    print("\n📝 Next steps:")
    print("1. Edit the .env file and set your Gibney credentials")
    print("2. Activate the virtual environment:")

    if os.name == "nt":  # Windows
        print("   venv\\Scripts\\activate")
    else:  # Unix/Linux/macOS
        print("   source venv/bin/activate")

    print("3. Start the backend server:")
    print("   python run_server.py")

    if frontend_setup_success:
        print("4. In a new terminal, start the frontend development server:")
        print("   cd frontend")
        print("   npm start")
        print("\n🌐 Backend API will be available at http://localhost:8000")
        print("🌐 Frontend will be available at http://localhost:3000")
        print("📚 API documentation will be at http://localhost:8000/docs")
    else:
        print("\n🌐 The backend server will be available at http://localhost:8000")
        print("📚 API documentation will be at http://localhost:8000/docs")
        print("⚠️  Frontend setup failed - you'll need to set it up manually")

    print("\n💡 To run background tasks manually (since Redis is disabled):")
    print(
        '   python -c "from app.worker import sync_scrape_all_users; sync_scrape_all_users()"'
    )


def main():
    """Main setup function"""
    print("🚀 Setting up Gibster development environment (Docker-free)...")
    print("=" * 60)

    # Check prerequisites
    check_python_version()
    node_available = check_node_version()

    # Backend setup
    setup_virtual_environment()
    install_dependencies()
    create_env_file()
    initialize_database()

    # Frontend setup
    frontend_setup_success = False
    if node_available:
        frontend_setup_success = install_frontend_dependencies()
    else:
        print("⚠️  Skipping frontend setup due to missing Node.js")

    # Final checks and instructions
    check_optional_services()
    print_next_steps(frontend_setup_success)


if __name__ == "__main__":
    main()
