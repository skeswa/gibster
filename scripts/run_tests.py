#!/usr/bin/env python3
"""
Simple test runner for Gibster - supports both backend and frontend tests with type checking
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


def run_backend_type_check(args):
    """Run mypy type checking on backend code"""
    print("\n🔍 Running backend type checking...")
    
    cmd = ["mypy", "backend", "--ignore-missing-imports"]
    
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

    args = parser.parse_args()

    # Validate mutually exclusive options
    if args.backend_only and args.frontend_only:
        print("❌ Cannot specify both --backend-only and --frontend-only")
        sys.exit(1)

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
