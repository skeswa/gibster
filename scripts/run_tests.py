#!/usr/bin/env python3
"""
Simple test runner for Gibster - supports both backend and frontend tests
"""
import argparse
import os
import subprocess
import sys


def run_command(cmd, cwd=None):
    """Run a command and return the exit code"""
    print(f"Running: {' '.join(cmd)}")
    if cwd:
        print(f"Working directory: {cwd}")
    result = subprocess.run(cmd, capture_output=False, cwd=cwd)
    return result.returncode


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
    parser = argparse.ArgumentParser(description="Run Gibster tests")
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

    args = parser.parse_args()

    # Validate mutually exclusive options
    if args.backend_only and args.frontend_only:
        print("❌ Cannot specify both --backend-only and --frontend-only")
        sys.exit(1)

    exit_codes = []

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
        print("\n✅ All tests passed!")
        if args.coverage:
            print("📊 Coverage reports generated:")
            if not args.frontend_only:
                print("   - Backend: htmlcov/index.html")
            if not args.backend_only:
                print("   - Frontend: frontend/coverage/lcov-report/index.html")
    else:
        print(f"\n❌ Tests failed with exit code {total_exit_code}")
        if not args.frontend_only and exit_codes[0] != 0:
            print("   - Backend tests failed")
        if not args.backend_only and (len(exit_codes) > 1 and exit_codes[-1] != 0):
            print("   - Frontend tests failed")
        sys.exit(total_exit_code)


if __name__ == "__main__":
    main()
