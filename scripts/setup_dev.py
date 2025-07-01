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
        f"{pip_path} install -r backend/requirements.txt", "Installing Python dependencies"
    )

    # Install Playwright browsers
    run_command(
        f"{python_path} -m playwright install chromium",
        "Installing Playwright Chromium browser",
    )


def setup_environment_file():
    """Create .env files from example if they don't exist"""
    # Create backend/.env
    backend_env_file = Path("backend/.env")
    backend_env_example = Path("backend/.env.example")
    
    if not backend_env_file.exists() and backend_env_example.exists():
        shutil.copy(backend_env_example, backend_env_file)
        print("✅ Created backend/.env file from backend/.env.example")
        print("⚠️  Please edit backend/.env file and set your values")
    elif backend_env_file.exists():
        print("✅ backend/.env file already exists")
    else:
        print("⚠️  No backend/.env.example found, you may need to create backend/.env manually")
    
    # Create frontend/.env.local
    frontend_env_file = Path("frontend/.env.local")
    frontend_env_example = Path("frontend/.env.example")
    
    if not frontend_env_file.exists() and frontend_env_example.exists():
        shutil.copy(frontend_env_example, frontend_env_file)
        print("✅ Created frontend/.env.local file from frontend/.env.example")
    elif frontend_env_file.exists():
        print("✅ frontend/.env.local file already exists")
    else:
        print("⚠️  No frontend/.env.example found, creating default frontend/.env.local")


def initialize_database():
    """Initialize the SQLite database"""
    # Determine the correct Python path
    if os.name == "nt":  # Windows
        python_path = "venv\\Scripts\\python"
    else:  # Unix/Linux/macOS
        python_path = "venv/bin/python"

    # Set PYTHONPATH to ensure backend module can be imported
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()

    result = subprocess.run(
        [python_path, "-c", "from backend.database import engine; from backend.models import Base; Base.metadata.create_all(bind=engine); print('Database tables created')"],
        capture_output=True,
        text=True,
        env=env
    )
    
    if result.returncode != 0:
        print(f"❌ Initializing SQLite database failed: {result.stderr}")
        return None
    
    print(f"✅ Initializing SQLite database completed successfully")
    return result


def check_optional_services():
    """Check for optional services like Redis"""
    print("\n🔍 Checking optional services:")

    # Check Redis
    redis_result = run_command("redis-cli ping", "Testing Redis connection")
    if redis_result and "PONG" in redis_result.stdout:
        print("✅ Redis is available - you can enable USE_CELERY=true in .env")
    else:
        print("ℹ️  Redis not available - background tasks will run synchronously")


def print_next_steps():
    """Print instructions for next steps"""
    print("\n🎉 Development environment setup complete!")
    print("\n📝 Next steps:")
    print("1. Edit the .env file and set your Gibney credentials")
    print("2. Activate the virtual environment:")

    if os.name == "nt":  # Windows
        print("   venv\\Scripts\\activate")
    else:  # Unix/Linux/macOS
        print("   source venv/bin/activate")

    print("3. Start the development server:")
    print("   python run_server.py")
    print("\n🌐 The server will be available at http://localhost:8000")
    print("📚 API documentation will be at http://localhost:8000/docs")


def main():
    """Main setup function"""
    print("🚀 Setting up Gibster development environment...")
    print("=" * 50)

    check_python_version()
    setup_virtual_environment()
    install_dependencies()
    setup_environment_file()
    initialize_database()
    check_optional_services()
    print_next_steps()


if __name__ == "__main__":
    main()
