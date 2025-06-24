#!/usr/bin/env python3
"""
Gibster Development Runner

Quick script to start both backend and frontend development servers.
"""

import os
import sys
import subprocess
import time
import signal
import threading
from pathlib import Path

# Add parent directory to Python path so we can import from app module
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def check_venv():
    """Check if running in virtual environment"""
    in_venv = hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )
    if not in_venv:
        print("⚠️  Warning: Not running in virtual environment")
        print(
            "   Run: source venv/bin/activate (or venv\\Scripts\\activate on Windows)"
        )
        print("   Then: python run_dev.py")
        return False
    return True


def check_env_file():
    """Check if .env file exists and has required variables"""
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found")
        print("   Run: python dev_setup.py")
        return False

    # Check for required Gibney credentials
    with open(env_file) as f:
        content = f.read()
        if "your-email@example.com" in content or "your-password" in content:
            print("⚠️  Please update .env with your actual Gibney credentials")
            print("   Edit GIBNEY_EMAIL and GIBNEY_PASSWORD in .env")

    return True


def check_database():
    """Check if database exists and is accessible"""
    try:
        from app.database import engine
        from app.models import Base

        # Test database connection
        with engine.connect() as conn:
            pass

        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        print("   Try running: python dev_setup.py")
        return False


def check_node():
    """Check if Node.js and npm are installed"""
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js version: {result.stdout.strip()}")
        else:
            print("❌ Node.js not found")
            print("   Install Node.js from https://nodejs.org/")
            return False

        result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ npm version: {result.stdout.strip()}")
        else:
            print("❌ npm not found")
            return False

        return True
    except FileNotFoundError:
        print("❌ Node.js/npm not found")
        print("   Install Node.js from https://nodejs.org/")
        return False


def check_frontend_deps():
    """Check if frontend dependencies are installed"""
    frontend_dir = Path("frontend")
    node_modules = frontend_dir / "node_modules"

    if not node_modules.exists():
        print("❌ Frontend dependencies not installed")
        print("   Run: cd frontend && npm install")
        return False

    print("✅ Frontend dependencies installed")
    return True


def main():
    """Main development runner"""
    print("🚀 Gibster Development Server")
    print("=" * 40)

    # Check virtual environment
    if not check_venv():
        sys.exit(1)

    # Check .env file
    if not check_env_file():
        sys.exit(1)

    # Check database
    if not check_database():
        sys.exit(1)

    # Check Node.js and npm
    if not check_node():
        sys.exit(1)

    # Check frontend dependencies
    if not check_frontend_deps():
        sys.exit(1)

    print("\n✅ All checks passed! Starting servers...")
    print("🖥️  Backend API: http://localhost:8000")
    print("📚 API docs: http://localhost:8000/docs")
    print("🌐 Frontend: http://localhost:3000")
    print("🛑 Press Ctrl+C to stop both servers\n")

    backend_process = None
    frontend_process = None

    def signal_handler(signum, frame):
        """Handle Ctrl+C by terminating both processes"""
        print("\n🛑 Stopping servers...")
        if backend_process:
            backend_process.terminate()
        if frontend_process:
            frontend_process.terminate()

        # Wait a bit for graceful shutdown
        time.sleep(1)

        if backend_process and backend_process.poll() is None:
            backend_process.kill()
        if frontend_process and frontend_process.poll() is None:
            frontend_process.kill()

        print("👋 Servers stopped")
        sys.exit(0)

    # Set up signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Start backend server as subprocess
        # Run from project root so it can import the app module
        project_root = Path(__file__).parent.parent

        # Set up environment with proper Python path
        backend_env = os.environ.copy()
        backend_env["PYTHONPATH"] = str(project_root)

        backend_process = subprocess.Popen(
            [sys.executable, "scripts/run_server.py"], cwd=project_root, env=backend_env
        )

        # Give backend a moment to start
        time.sleep(2)

        # Start frontend server as subprocess
        frontend_dir = Path("frontend")
        env = os.environ.copy()
        env["BROWSER"] = "none"  # Prevent auto-opening browser

        frontend_process = subprocess.Popen(
            ["npm", "run", "dev"], cwd=frontend_dir, env=env
        )

        # Wait for both processes
        while True:
            # Check if either process has died
            if backend_process.poll() is not None:
                print("❌ Backend server stopped unexpectedly")
                break
            if frontend_process.poll() is not None:
                print("❌ Frontend server stopped unexpectedly")
                break

            time.sleep(1)

    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        signal_handler(signal.SIGTERM, None)


if __name__ == "__main__":
    main()
