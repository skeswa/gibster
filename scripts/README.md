# Scripts

This directory contains utility scripts for the Gibster project.

## Code Formatting

### `format.sh`

Formats all code in the repository using appropriate tools for each language:

- **Python**: Uses `black` and `isort` for code formatting and import sorting
- **Frontend**: Uses `prettier` for TypeScript/JavaScript/CSS formatting
- **Shell scripts**: Uses `shfmt` (optional) for shell script formatting

**Usage:**

```bash
./scripts/format.sh
```

**Prerequisites:**

- Python packages: `black` and `isort` (automatically installed with `pip install -r backend/requirements.txt`)
- Node.js and npm (for frontend formatting)
- `shfmt` (optional, for shell script formatting)

### `format-check.sh`

Checks if all code is properly formatted without making any changes. Useful for CI/CD pipelines.

**Usage:**

```bash
./scripts/format-check.sh
```

Returns exit code 0 if all code is properly formatted, exit code 1 if formatting issues are found.

## Configuration

- **Python formatting**: Configured in `backend/pyproject.toml`
- **Frontend formatting**: Configured in `frontend/.prettierrc`

## Integration with Development Workflow

### Pre-commit Hook

You can add the format script as a pre-commit hook:

```bash
# In .git/hooks/pre-commit
#!/bin/bash
./scripts/format.sh
```

### CI/CD Integration

Use the format-check script in your CI pipeline to ensure all code is properly formatted:

```yaml
# Example GitHub Actions step
- name: Check code formatting
  run: ./scripts/format-check.sh
```

## Scripts Overview

### Core Scripts

- **`main.py`** - Original scraping script that generates iCal files from Gibney rentals
- **`run_server.py`** - Starts the FastAPI development server
- **`run_dev.py`** - Development runner with environment checks
- **`run_tests.py`** - Unified test runner for both backend (Python/pytest) and frontend (JavaScript/Jest) tests with type checking (mypy/tsc) and various options (unit, integration, coverage)
- **`run_worker.py`** - Celery worker for background tasks

### Setup Scripts

- **`setup.py`** - Full development environment setup
- **`dev_setup.py`** - Docker-free development setup
- **`setup_dev.py`** - Alternative development setup script

### Testing Scripts

- **`test_scraper.py`** - Test script for scraper functionality with Gibney credentials

### Test Runner (`run_tests.py`)

The unified test runner supports both backend and frontend testing with **type checking enabled by default**:

#### Available Options

```bash
# Run all tests (backend + frontend) with type checking
python3 run_tests.py

# Backend only with type checking
python3 run_tests.py --backend-only

# Frontend only with type checking
python3 run_tests.py --frontend-only

# Skip type checking (tests only)
python3 run_tests.py --skip-type-check

# Type checking only (no tests)
python3 run_tests.py --type-check-only

# With coverage reports
python3 run_tests.py --coverage

# Verbose output
python3 run_tests.py --verbose

# Backend test types (unit/integration)
python3 run_tests.py --backend-only --type unit
python3 run_tests.py --backend-only --type integration
```

#### Type Checking

- **Backend**: Uses `mypy` for Python type checking
- **Frontend**: Uses TypeScript compiler (`tsc`) for type checking
- Type checking runs automatically before tests (unless `--skip-type-check` is used)
- Type errors will prevent tests from running

#### Test Detection

- **Backend**: Automatically runs pytest for Python tests
- **Frontend**: Automatically detects and runs Jest tests in `frontend/` directory
- **Coverage**: Generates separate coverage reports for backend and frontend

#### Coverage Reports

- Backend: `htmlcov/index.html`
- Frontend: `frontend/coverage/lcov-report/index.html`

## Usage

All scripts can be run from either the root directory or the scripts directory:

### From Root Directory

```bash
python3 scripts/run_server.py
python3 scripts/run_tests.py --help
python3 scripts/setup.py
```

### From Scripts Directory

```bash
cd scripts
python3 run_server.py
python3 run_tests.py --help
python3 setup.py
```

## Path Adjustments

The scripts have been updated to work correctly from their new location:

- Path references to `resources/` and `backend/` directories are properly adjusted
- Import statements have been updated to work from the new location
- All relative paths maintain compatibility with the project structure

## Dependencies

Some scripts require additional dependencies to be installed:

- Run `pip install -r backend/requirements.txt` from the root directory
- For Playwright scripts: `playwright install chromium`
