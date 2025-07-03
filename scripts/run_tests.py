#!/usr/bin/env python3
"""
Simple test runner for Gibster - supports both backend and frontend tests with type checking

Supports running unit, integration, and end-to-end tests.
"""
import argparse
import os
import shutil
import subprocess
import sys


def check_virtual_env():
    """Check if virtual environment is activated and required tools are available"""
    # Check multiple indicators of venv activation
    in_venv = (
        hasattr(sys, 'prefix') and sys.prefix != sys.base_prefix or
        os.environ.get('VIRTUAL_ENV') is not None or
        sys.executable.startswith(os.path.join(os.getcwd(), 'venv')) or
        sys.executable.startswith(os.path.join(os.getcwd(), '.venv'))
    )
    
    # Also check if we're running the script with the venv Python but tools aren't in PATH
    venv_python_but_no_activation = (
        (sys.executable.startswith(os.path.join(os.getcwd(), 'venv')) or
         sys.executable.startswith(os.path.join(os.getcwd(), '.venv'))) and
        os.environ.get('VIRTUAL_ENV') is None
    )
    
    if venv_python_but_no_activation:
        print("⚠️  Warning: Running with venv Python but environment not fully activated!")
        print("   PATH may not include venv binaries.")
        print("\nTo properly activate the virtual environment, run:")
        print("  source venv/bin/activate")
        print("\nAttempting to continue anyway...\n")
    elif not in_venv:
        print("⚠️  Warning: Virtual environment is not activated!")
        print("\nTo activate the virtual environment, run:")
        print("  source venv/bin/activate")
        print("\nAttempting to continue anyway...\n")
    
    # Check for required tools - but also check venv paths
    required_tools = {
        'mypy': 'Type checking',
        'pytest': 'Running tests',
        'npm': 'Frontend tests'
    }
    
    missing_tools = []
    for tool, purpose in required_tools.items():
        # Check system PATH
        found = shutil.which(tool)
        
        # Also check venv paths for Python tools
        if not found and tool in ['mypy', 'pytest']:
            venv_paths = [
                os.path.join(os.getcwd(), "venv", "bin", tool),
                os.path.join(os.getcwd(), ".venv", "bin", tool)
            ]
            for venv_path in venv_paths:
                if os.path.exists(venv_path):
                    found = True
                    break
        
        if not found:
            missing_tools.append((tool, purpose))
    
    if missing_tools:
        print("❌ Missing required tools:")
        for tool, purpose in missing_tools:
            print(f"  - {tool} (needed for: {purpose})")
        
        if not in_venv:
            print("\n💡 Tip: Activating the virtual environment should resolve Python tool issues.")
            print("   Run: source venv/bin/activate")
        return False
    
    return True


def run_command(cmd, cwd=None):
    """Run a command and return the exit code"""
    print(f"Running: {' '.join(cmd)}")
    if cwd:
        print(f"Working directory: {cwd}")
    
    try:
        result = subprocess.run(cmd, capture_output=False, cwd=cwd)
        return result.returncode
    except FileNotFoundError as e:
        print(f"\n❌ Error: Command '{cmd[0]}' not found!")
        if cmd[0] in ['mypy', 'pytest']:
            print("\n💡 This is likely because the virtual environment is not activated.")
            print("   Run: source venv/bin/activate")
        return 1


def run_backend_type_check(args):
    """Run mypy type checking on backend code"""
    print("\n🔍 Running backend type checking...")
    
    # Try to find mypy in venv first, then fall back to system
    venv_mypy = os.path.join(os.getcwd(), "venv", "bin", "mypy")
    venv_mypy_alt = os.path.join(os.getcwd(), ".venv", "bin", "mypy")
    
    if os.path.exists(venv_mypy):
        mypy_cmd = venv_mypy
    elif os.path.exists(venv_mypy_alt):
        mypy_cmd = venv_mypy_alt
    else:
        mypy_cmd = "mypy"
    
    cmd = [mypy_cmd, "backend", "--ignore-missing-imports"]
    
    if args.verbose:
        cmd.append("--verbose")
    
    return run_command(cmd)


def run_backend_tests(args):
    """Run Python backend tests with pytest"""
    print("\n🔧 Running backend tests...")

    # Base pytest command
    cmd = ["python3", "-m", "pytest", "backend"]

    # Add verbosity
    if args.verbose:
        cmd.append("-v")

    # Add coverage if requested
    if args.coverage:
        cmd.extend(["--cov=backend", "--cov-report=html", "--cov-report=term"])

    # Add test type filter
    if args.type == "unit":
        cmd.extend(["-m", "unit"])
    elif args.type == "integration":
        cmd.extend(["-m", "integration"])

    return run_command(cmd)


def run_e2e_tests(args):
    """Run end-to-end tests against real Gibney site"""
    print("\n🌐 Running end-to-end tests...")
    print("⚠️  These tests connect to the real Gibney website!")
    
    # Check for credentials (the test script will load from .env if available)
    email = os.environ.get("GIBNEY_EMAIL")
    password = os.environ.get("GIBNEY_PASSWORD")
    
    # Check if .env file exists
    env_path = os.path.join("backend", ".env")
    env_exists = os.path.exists(env_path)
    
    if not email or not password:
        print("\n⚠️  No test credentials found in environment!")
        if env_exists:
            print("   The test will attempt to load from backend/.env")
        else:
            print("\n❌ E2E tests require Gibney credentials!")
            print("\nPlease provide credentials in one of these ways:")
            print("\n1. Add to backend/.env file:")
            print("   GIBNEY_EMAIL=your-gibney-email")
            print("   GIBNEY_PASSWORD=your-gibney-password")
            print("\n2. Set environment variables:")
            print("   export GIBNEY_EMAIL='your-gibney-email'")
            print("   export GIBNEY_PASSWORD='your-gibney-password'")
            print("\nThen run the tests again.")
            # Don't fail here - let the test script handle it
    
    # Run the e2e test script directly
    cmd = ["python3", "backend/tests/test_scraper_e2e.py"]
    
    return run_command(cmd)


def run_frontend_type_check(args):
    """Run TypeScript type checking on frontend code"""
    print("\n🔍 Running frontend type checking...")
    
    frontend_dir = "frontend"
    
    # Check if frontend directory exists
    if not os.path.exists(frontend_dir):
        print(
            f"⚠️  Frontend directory '{frontend_dir}' not found, skipping frontend type checking"
        )
        return 0
    
    # Check if tsconfig.json exists
    tsconfig_path = os.path.join(frontend_dir, "tsconfig.json")
    if not os.path.exists(tsconfig_path):
        print(f"⚠️  No tsconfig.json found in '{frontend_dir}', skipping frontend type checking")
        return 0
    
    cmd = ["npm", "run", "type-check"]
    
    return run_command(cmd, cwd=frontend_dir)


def run_frontend_tests(args):
    """Run JavaScript/TypeScript frontend tests with Jest"""
    print("\n⚛️  Running frontend tests...")

    frontend_dir = "frontend"

    # Check if frontend directory exists
    if not os.path.exists(frontend_dir):
        print(
            f"⚠️  Frontend directory '{frontend_dir}' not found, skipping frontend tests"
        )
        return 0

    # Check if package.json exists
    package_json_path = os.path.join(frontend_dir, "package.json")
    if not os.path.exists(package_json_path):
        print(f"⚠️  No package.json found in '{frontend_dir}', skipping frontend tests")
        return 0

    # Build npm test command
    if args.coverage:
        cmd = ["npm", "run", "test:coverage"]
    else:
        cmd = ["npm", "test"]

    # Add Jest flags for non-interactive mode
    cmd.extend(["--", "--watchAll=false"])

    if args.verbose:
        cmd.extend(["--verbose"])

    return run_command(cmd, cwd=frontend_dir)


def main():
    # Check environment before parsing args
    env_ok = check_virtual_env()
    
    parser = argparse.ArgumentParser(description="Run Gibster tests with optional type checking")
    parser.add_argument(
        "--type",
        choices=["unit", "integration", "all"],
        default="all",
        help="Type of tests to run (default: all) - only applies to backend tests",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--coverage", action="store_true", help="Run with coverage report"
    )
    parser.add_argument(
        "--backend-only", action="store_true", help="Run only backend tests"
    )
    parser.add_argument(
        "--frontend-only", action="store_true", help="Run only frontend tests"
    )
    parser.add_argument(
        "--skip-type-check", action="store_true", help="Skip type checking (type checking is on by default)"
    )
    parser.add_argument(
        "--type-check-only", action="store_true", help="Run only type checking, no tests"
    )
    parser.add_argument(
        "--e2e", action="store_true", help="Run end-to-end tests against real Gibney site (requires credentials)"
    )

    args = parser.parse_args()

    # Validate mutually exclusive options
    if args.backend_only and args.frontend_only:
        print("❌ Cannot specify both --backend-only and --frontend-only")
        sys.exit(1)
    
    # Handle e2e tests separately
    if args.e2e:
        if args.skip_type_check or args.type_check_only or args.coverage:
            print("❌ E2E tests cannot be combined with other test options")
            sys.exit(1)
        
        exit_code = run_e2e_tests(args)
        if exit_code == 0:
            print("\n✅ E2E tests passed!")
        else:
            print("\n❌ E2E tests failed")
        sys.exit(exit_code)

    exit_codes = []
    type_check_failed = False

    # Run type checking by default (unless skipped)
    if not args.skip_type_check or args.type_check_only:
        # Backend type checking
        if not args.frontend_only:
            backend_type_exit_code = run_backend_type_check(args)
            if backend_type_exit_code != 0:
                type_check_failed = True
                print("❌ Backend type checking failed")
            exit_codes.append(backend_type_exit_code)
        
        # Frontend type checking
        if not args.backend_only:
            frontend_type_exit_code = run_frontend_type_check(args)
            if frontend_type_exit_code != 0:
                type_check_failed = True
                print("❌ Frontend type checking failed")
            exit_codes.append(frontend_type_exit_code)
        
        # If type-check-only, don't run tests
        if args.type_check_only:
            total_exit_code = sum(exit_codes)
            if total_exit_code == 0:
                print("\n✅ All type checks passed!")
            else:
                print(f"\n❌ Type checking failed with exit code {total_exit_code}")
            sys.exit(total_exit_code)

    # Run tests only if type checking passed or wasn't requested
    if not type_check_failed:
        # Run backend tests
        if not args.frontend_only:
            backend_exit_code = run_backend_tests(args)
            exit_codes.append(backend_exit_code)

        # Run frontend tests
        if not args.backend_only:
            frontend_exit_code = run_frontend_tests(args)
            exit_codes.append(frontend_exit_code)

    # Summary
    total_exit_code = sum(exit_codes)

    if total_exit_code == 0:
        if args.skip_type_check:
            print("\n✅ All tests passed!")
        else:
            print("\n✅ All type checks and tests passed!")
        if args.coverage:
            print("📊 Coverage reports generated:")
            if not args.frontend_only:
                print("   - Backend: htmlcov/index.html")
            if not args.backend_only:
                print("   - Frontend: frontend/coverage/lcov-report/index.html")
    else:
        print(f"\n❌ Failed with exit code {total_exit_code}")
        # Provide detailed failure info
        if type_check_failed:
            print("   - Type checking failed (tests were skipped)")
        else:
            # Determine which tests failed based on position in exit_codes
            if not args.skip_type_check:
                # With type checking, tests come after type checks
                backend_offset = 2 if not args.frontend_only else 0
                frontend_offset = 3 if not args.backend_only and not args.frontend_only else 1
            else:
                backend_offset = 0
                frontend_offset = 1
            
            if not args.frontend_only and len(exit_codes) > backend_offset and exit_codes[backend_offset] != 0:
                print("   - Backend tests failed")
            if not args.backend_only and len(exit_codes) > frontend_offset and exit_codes[frontend_offset] != 0:
                print("   - Frontend tests failed")
        
        sys.exit(total_exit_code)


if __name__ == "__main__":
    main()
