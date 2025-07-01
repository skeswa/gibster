# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Gibster synchronizes Gibney dance space bookings with personal calendars. It consists of:

- **Backend**: FastAPI (Python) REST API with PostgreSQL/SQLite
- **Frontend**: Next.js 15 (TypeScript) React application
- **Scraper**: Playwright-based Gibney website scraper
- **Background Tasks**: Celery with Redis (production) or synchronous (development)

## Essential Commands

**Important**: Always use absolute paths when running commands to avoid path confusion. The development SQLite database (`gibster_dev.db`) is located in the `backend/` directory and should only be accessed from there.

### Backend Development

```bash
# Setup and run
source venv/bin/activate         # Activate virtual environment
python scripts/dev_setup.py      # One-time automated setup
python scripts/run_server.py     # Start development server (port 8000)

# Testing
python scripts/run_tests.py --coverage   # Run all tests with coverage
python scripts/run_tests.py --backend-only --type unit  # Unit tests only
pytest -v backend/tests/test_some_file.py::test_function  # Run specific test

# Code quality
black backend/                   # Format Python code
isort backend/                   # Sort imports

# Database
cd backend && alembic upgrade head       # Run migrations
# Note: Always run database commands from the backend/ directory
# The SQLite database file is at backend/gibster_dev.db
```

### Kubernetes Deployment

```bash
# Local development
kubectl apply -k k8s/overlays/development

# Production (via CI/CD)
git push origin main            # Triggers GitHub Actions deployment

# Manual production
kubectl apply -k k8s/overlays/production

# Check deployment
kubectl get pods -l app=gibster
kubectl logs -l component=backend -f
```

### Frontend Development

```bash
cd frontend
npm run dev                     # Start development server (port 3000)
npm run build                   # Production build
npm test                        # Run tests
npm run lint                    # Run ESLint
npm run type-check              # TypeScript type checking
npm run format                  # Prettier formatting
```

## Architecture Overview

### Data Flow

1. User interacts with Next.js frontend (port 3000)
2. Frontend makes API calls to FastAPI backend (proxied to port 8000)
3. Backend authenticates users via JWT tokens
4. Backend stores encrypted Gibney credentials in database
5. Celery workers (or sync tasks in dev) scrape Gibney website using Playwright
   - Scraper handles pagination automatically to fetch all bookings across multiple pages
6. Calendar feed (.ics) is generated and made available for subscription

### Key Architectural Decisions

- **Authentication**: JWT tokens with bcrypt password hashing
- **Credential Storage**: Gibney credentials encrypted with Fernet
- **Database**: SQLAlchemy ORM with async support
- **Frontend Routing**: Next.js App Router with client-side navigation
- **API Design**: RESTful with automatic OpenAPI documentation at /docs
- **Testing**: Separate unit/integration tests with pytest markers

### Project Structure

```
gibster/
├── backend/
│   ├── app/           # Main application code
│   │   ├── api/       # API routes
│   │   ├── core/      # Core utilities (config, security)
│   │   ├── crud/      # Database operations
│   │   ├── models/    # SQLAlchemy models
│   │   └── schemas/   # Pydantic schemas
│   ├── tests/         # Backend tests
│   ├── logs/          # Application logs
│   ├── alembic/       # Database migrations
│   ├── requirements.txt # Python dependencies
│   ├── pyproject.toml  # Python project config
│   ├── pytest.ini      # Pytest configuration
│   └── gibster_dev.db  # SQLite development database
├── frontend/
│   ├── app/           # Next.js app directory
│   ├── components/    # React components
│   ├── lib/           # Utilities and API client
│   └── __tests__/     # Frontend tests
├── k8s/               # Kubernetes manifests
│   ├── base/          # Base resources
│   └── overlays/      # Environment-specific configs
└── .github/
    └── workflows/     # GitHub Actions CI/CD
```

### Development Configuration

- Backend environment variables in `backend/.env` (copy from `backend/.env.example`)
- Frontend environment variables in `frontend/.env.local` (copy from `frontend/.env.example`)
- Backend config: `backend/app/core/config.py`
- Frontend config: `frontend/next.config.ts`
- Test markers: `unit`, `integration` in `backend/pytest.ini`

### Important Development Notes

1. **Database Location**: In development, the SQLite database is always located at `backend/gibster_dev.db`. Never reference or create database files outside the backend directory.

2. **Path Usage**: Always use absolute paths when running commands or referencing files to avoid confusion. For example:
   - Good: `/Users/username/repos/gibster/backend/gibster_dev.db`
   - Good: `cd /Users/username/repos/gibster/backend && alembic upgrade head`
   - Bad: `../gibster_dev.db` or relative paths that might create files in wrong locations

3. **Database Commands**: Always execute database-related commands (migrations, sqlite3 commands) from within the `backend/` directory to ensure the correct database file is used.
