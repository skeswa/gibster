# Gibster Scripts

This directory contains all the utility scripts for the Gibster project.

## Scripts Overview

### Core Scripts
- **`main.py`** - Original scraping script that generates iCal files from Gibney rentals
- **`run_server.py`** - Starts the FastAPI development server
- **`run_dev.py`** - Development runner with environment checks
- **`run_tests.py`** - Unified test runner for both backend (Python/pytest) and frontend (JavaScript/Jest) tests with various options (unit, integration, coverage)
- **`run_worker.py`** - Celery worker for background tasks

### Setup Scripts
- **`setup.py`** - Full development environment setup
- **`dev_setup.py`** - Docker-free development setup
- **`setup_dev.py`** - Alternative development setup script

### Testing Scripts
- **`test_scraper.py`** - Test script for scraper functionality with Gibney credentials

### Test Runner (`run_tests.py`)

The unified test runner supports both backend and frontend testing:

#### Available Options
```bash
# Run all tests (backend + frontend)
python3 run_tests.py

# Backend only
python3 run_tests.py --backend-only

# Frontend only  
python3 run_tests.py --frontend-only

# With coverage reports
python3 run_tests.py --coverage

# Verbose output
python3 run_tests.py --verbose

# Backend test types (unit/integration)
python3 run_tests.py --backend-only --type unit
python3 run_tests.py --backend-only --type integration
```

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
- Path references to `resources/` and `app/` directories are properly adjusted
- Import statements have been updated to work from the new location
- All relative paths maintain compatibility with the project structure

## Dependencies

Some scripts require additional dependencies to be installed:
- Run `pip install -r requirements.txt` from the root directory
- For Playwright scripts: `playwright install chromium` 