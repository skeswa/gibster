# Gibster Scripts

This directory contains all the utility scripts for the Gibster project.

## Scripts Overview

### Core Scripts
- **`main.py`** - Original scraping script that generates iCal files from Gibney rentals
- **`run_server.py`** - Starts the FastAPI development server
- **`run_dev.py`** - Development runner with environment checks
- **`run_tests.py`** - Test runner with various options (unit, integration, coverage)
- **`run_worker.py`** - Celery worker for background tasks

### Setup Scripts
- **`setup.py`** - Full development environment setup
- **`dev_setup.py`** - Docker-free development setup
- **`setup_dev.py`** - Alternative development setup script

### Testing Scripts
- **`test_scraper.py`** - Test script for scraper functionality with Gibney credentials

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