# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Gibster synchronizes Gibney dance space bookings with personal calendars. It consists of:

- **Backend**: FastAPI (Python) REST API with PostgreSQL/SQLite
- **Frontend**: Next.js 15 (TypeScript) React application
- **Scraper**: Playwright-based Gibney website scraper
- **Background Tasks**: Celery with Redis (production) or synchronous (development)

## Critical Documentation

**⚠️ IMPORTANT**: Before making any architectural or design decisions, you MUST consult these essential documentation files:

### 📐 Architecture Documentation (`docs/architecture.md`)

This comprehensive document provides:

- System overview with detailed component diagrams
- Tech stack specifications and justifications
- Core component designs (authentication, data models, scraper, calendar integration)
- Data flow diagrams for all major operations
- Security architecture and performance optimizations
- API design patterns and database schema
- Deployment architecture for development and production
- Design decisions and future considerations

### 📋 Requirements Documentation (`docs/requirements.md`)

This detailed requirements specification includes:

- Complete functional requirements with requirement IDs (FR-x.x.x)
- Non-functional requirements covering security, performance, reliability, usability, maintainability, compatibility, and operations
- Technical constraints and infrastructure requirements
- Clear acceptance criteria for all features
- Traceability through requirement identifiers

**Always reference these documents when:**

- Making architectural changes or design decisions
- Implementing new features or modifying existing ones
- Evaluating technical approaches or trade-offs
- Understanding system constraints and requirements
- Ensuring consistency with established patterns

## Essential Commands

**Important**: Always use absolute paths when running commands to avoid path confusion. The development SQLite database (`gibster_dev.db`) is located in the `backend/` directory and should only be accessed from there.

### Backend Development

```bash
# Setup and run
source venv/bin/activate         # Activate virtual environment
python scripts/dev_setup.py      # One-time automated setup
python scripts/run_server.py     # Start development server (port 8000)

# Code quality
black backend/                   # Format Python code
isort backend/                   # Sort imports
mypy backend --ignore-missing-imports  # Run type checking manually

# Database
cd backend && alembic upgrade head       # Run migrations
# Note: Always run database commands from the backend/ directory
# The SQLite database file is at backend/gibster_dev.db
```

### Testing

#### Test Structure

- `backend/tests/test_*.py` - Unit and integration tests (run automatically in CI)
- `backend/tests/test_scraper_e2e.py` - End-to-end tests against real Gibney website (manual only)
- `frontend/__tests__/` - Frontend component and integration tests

#### Running Tests

```bash
# Run all tests with type checking (default)
python scripts/run_tests.py

# Backend-specific tests
python scripts/run_tests.py --backend-only --type unit  # Type check + unit tests only
python scripts/run_tests.py --backend-only --type integration  # Integration tests only

# Frontend-specific tests
python scripts/run_tests.py --frontend-only

# Test options
python scripts/run_tests.py --coverage   # Run with coverage reports
python scripts/run_tests.py --skip-type-check  # Skip type checking, tests only
python scripts/run_tests.py --type-check-only  # Type checking only, no tests

# Run specific test directly
pytest -v backend/tests/test_some_file.py::test_function  # No type check
```

#### End-to-End Tests

The E2E tests connect to the real Gibney website to verify the scraper works correctly.

**Setup:**

Option 1: Add Gibney credentials to `backend/.env` file:

```bash
# Add to backend/.env
GIBNEY_EMAIL=your-email@example.com
GIBNEY_PASSWORD=your-password
```

Option 2: Set environment variables:

```bash
export GIBNEY_EMAIL="your-email@example.com"
export GIBNEY_PASSWORD="your-password"
```

Note: These are the same credentials used for development/testing throughout the application.

**Run E2E tests:**

```bash
# Using the test runner (will automatically load from backend/.env)
python scripts/run_tests.py --e2e

# Or run directly
python backend/tests/test_scraper_e2e.py
```

The E2E tests will:

1. Test login functionality with visual browser (headless=False)
2. Verify post-login navigation
3. Test full booking scraping
4. Display found bookings

#### Test Markers

Backend tests use pytest markers for categorization:

- `@pytest.mark.unit` - Fast unit tests (no external dependencies)
- `@pytest.mark.integration` - Tests that may use database or other services

#### Debugging Scraper Issues

When the scraper fails, it creates debug files in the project root:

- `debug_*.png` - Screenshots of the page at failure point
- `debug_*.html` - HTML content of the page for inspection

The E2E tests run with `headless=False` for the login test, allowing you to watch the browser interaction in real-time.

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

#### Theme System

The frontend includes a comprehensive dark mode theme system built with:

- **next-themes**: For theme management and persistence
- **Tailwind CSS**: With class-based dark mode (`darkMode: ["class"]`)
- **CSS Variables**: For dynamic color theming

##### Theme Components

**ThemeProvider** (`/src/app/providers/ThemeProvider.tsx`)

- Wraps the application and provides theme context
- Enables system preference detection and localStorage persistence
- Prevents flash on reload with `suppressHydrationWarning`

**Theme Toggle Components**:

- `ThemeToggle` - Button group for light/dark/system selection
- `ThemeDropdown` - Dropdown menu for theme switching
- `ThemeSelect` - Native select element (most accessible)

**Custom Hook** (`/src/hooks/useThemeState.ts`):

```typescript
const { theme, setTheme, currentTheme, isDarkMode, mounted } = useThemeState();
```

##### Usage Examples

Basic theme toggle:

```tsx
import { ThemeToggle } from '@/components/ThemeToggle';

function Header() {
  return (
    <header>
      <ThemeToggle />
    </header>
  );
}
```

Theme-aware styling:

```tsx
<div className='bg-white dark:bg-gray-900'>
  <p className='text-black dark:text-white'>Theme-aware text</p>
</div>
```

Conditional rendering:

```tsx
const { isDarkMode, mounted } = useThemeState();
if (!mounted) return null; // Avoid hydration mismatch

return <div>{isDarkMode ? 'Dark mode' : 'Light mode'}</div>;
```

##### Theme Demo

Visit `/theme-demo` in development to see all themed components in action.

##### Best Practices

1. Always check `mounted` state before rendering theme-dependent content
2. Use the `dark:` Tailwind modifier for conditional dark mode styles
3. Prefer CSS variables for colors to ensure consistency
4. Test both light and dark modes when developing new components

## Architecture Overview

### Data Flow

1. User interacts with Next.js frontend (port 3000)
2. Frontend makes API calls to FastAPI backend (proxied to port 8000)
3. Backend authenticates users via JWT tokens
4. Backend stores encrypted Gibney credentials in database
5. Celery workers (or sync tasks in dev) scrape Gibney website using Playwright
   - Scraper handles infinite scroll automatically by scrolling to the bottom of the page
   - When scrolled to bottom, the page loads more bookings via JavaScript
   - Uses progressive wait strategy with multiple retry attempts to ensure content loads
   - Detects and waits for loading spinners when present
   - Scraper continues scrolling until no new content is loaded after multiple attempts
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
- Theme CSS variables: `frontend/src/globals.css`
- Tailwind dark mode config: `frontend/tailwind.config.js` with `darkMode: ["class"]`
- Test markers: `unit`, `integration` in `backend/pytest.ini`

### Important Development Notes

1. **Database Location**: In development, the SQLite database is always located at `backend/gibster_dev.db`. Never reference or create database files outside the backend directory.

2. **Path Usage**: Always use absolute paths when running commands or referencing files to avoid confusion. For example:
   - Good: `/Users/username/repos/gibster/backend/gibster_dev.db`
   - Good: `cd /Users/username/repos/gibster/backend && alembic upgrade head`
   - Bad: `../gibster_dev.db` or relative paths that might create files in wrong locations

3. **Database Commands**: Always execute database-related commands (migrations, sqlite3 commands) from within the `backend/` directory to ensure the correct database file is used.

4. **Type Checking**: The test runner (`scripts/run_tests.py`) runs type checking by default before tests:
   - Backend uses `mypy` for Python type checking
   - Frontend uses `tsc` for TypeScript type checking
   - Type errors will prevent tests from running
   - Use `--skip-type-check` to bypass type checking when needed
   - Run `mypy backend --ignore-missing-imports` to check types manually

5. **Datetime Usage**: Always use timezone-aware datetimes to avoid timezone-related bugs:
   - **DO NOT USE**: `datetime.utcnow()` - This is deprecated and creates timezone-naive datetimes
   - **USE INSTEAD**: `datetime.now(timezone.utc)` - Creates timezone-aware UTC datetimes
   - Always import `timezone` from datetime: `from datetime import datetime, timezone`
   - This prevents "can't subtract offset-naive and offset-aware datetimes" errors
   - All datetime objects in the codebase should be timezone-aware for consistency
