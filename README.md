# Gibster

A service to synchronize Gibney dance space bookings with your personal calendar.

## What is Gibster?

For dancers who frequently book rehearsal space at Gibney, keeping track of upcoming reservations can be cumbersome. The current booking portal, while functional, presents bookings in a simple list format that is difficult to parse at a glance and does not integrate with personal calendar applications.

Gibster solves this by providing a "set it and forget it" service. You provide your Gibney login credentials once, and Gibster periodically scrapes your bookings, making them available via a standard calendar subscription link (iCal). This allows you to view all your bookings directly in your preferred calendar app, providing a consolidated and user-friendly view of your schedule.

## How It Works

```mermaid
graph TD
    A[You provide Gibney credentials] --> B[Gibster securely stores them]
    B --> C[Background worker scrapes bookings every 2 hours]
    C --> D[Bookings converted to calendar events]
    D --> E[Your calendar app syncs automatically]
    E --> F[See Gibney bookings in Google Calendar, Apple Calendar, etc.]
```

## Architecture

The system consists of four main components:

1. **Frontend (React)** - User interface for account management and viewing bookings
2. **Backend API (FastAPI)** - REST API for user management and calendar generation
3. **Scraper Worker (Celery)** - Background service for scraping Gibney bookings
4. **Database (PostgreSQL/SQLite)** - Stores user data and scraped bookings

```mermaid
graph TD
    A[User Browser] --> B[React Frontend]
    B --> C[FastAPI Backend]
    C --> D[PostgreSQL Database]
    C --> E[Calendar Feed]
    F[Celery Worker] --> G[Gibney Website]
    F --> D
    H[Calendar App] --> E
```

## Features

- **Secure credential storage** - Gibney passwords encrypted at rest
- **Automatic syncing** - Bookings updated every 2 hours
- **Universal calendar compatibility** - Works with Google Calendar, Apple Calendar, Outlook, etc.
- **Web dashboard** - Manage settings and view sync status
- **Manual sync** - Trigger immediate updates when needed

## Quick Start

### Local Development (Recommended)

```bash
git clone <your-repo-url>
cd gibster
python dev_setup.py  # Automated Docker-free setup
# Edit .env with your Gibney credentials (created from .env.example)
source venv/bin/activate  # On Windows: venv\Scripts\activate
python run_server.py
```

Access at http://localhost:8000

The setup script automatically:
- Creates virtual environment
- Installs all Python dependencies
- Installs Playwright browser
- Creates SQLite database
- Creates `.env` file from `.env.example` template
- Checks for optional services (Redis)

**Important:** After setup, edit `.env` and add your actual Gibney credentials and generate secure keys for production use.

### Using Kubernetes (Production)

```bash
git clone <your-repo-url>
cd gibster

# For local K3s development
kubectl apply -k k8s/overlays/development

# Production deployment is automated via GitHub Actions
# See k8s/README.md for detailed instructions
```

**Note:** The Kubernetes setup uses PostgreSQL StatefulSet and Redis deployment. For local development without Kubernetes, use the dev_setup.py script which uses SQLite and runs background tasks synchronously.

## Usage

1. **Register** at http://localhost:8000
2. **Add Gibney credentials** in Settings
3. **Copy calendar URL** from dashboard
4. **Subscribe in your calendar app:**
   - **Google Calendar:** Settings → Add calendar → From URL
   - **Apple Calendar:** File → New Calendar Subscription
   - **Outlook:** Calendar → Add calendar → Subscribe from web

## Development

### Running Tests

The test runner now supports both backend (Python) and frontend (JavaScript/TypeScript) tests:

```bash
# Activate virtual environment first
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run ALL tests (backend + frontend) with coverage
python run_tests.py --coverage

# Run only backend tests
python run_tests.py --backend-only --coverage

# Run only frontend tests  
python run_tests.py --frontend-only --coverage

# Run specific backend test types
python run_tests.py --backend-only --type unit
python run_tests.py --backend-only --type integration

# Run with verbose output
python run_tests.py --verbose

# Using pytest directly (backend only)
pytest -v --cov=app
```

The test runner automatically detects and runs:
- **Backend tests**: Python tests using pytest
- **Frontend tests**: React component tests using Jest + Testing Library

**Coverage Reports:**
- Backend: `htmlcov/index.html`
- Frontend: `frontend/coverage/lcov-report/index.html`

### Frontend Development

The frontend has been migrated from Create React App to **Next.js with TypeScript** for improved performance, better developer experience, and modern tooling.

```bash
cd frontend
npm install
npm run dev        # Start development server (Next.js)
npm run build      # Build for production
npm run start      # Start production server
npm test           # Run component tests
npm run test:watch # Run tests in watch mode
npm run lint       # Run ESLint
npm run type-check # TypeScript type checking
```

Frontend available at http://localhost:3000 with API proxy to backend.

**Key Features of the Next.js Migration:**
- **TypeScript Support**: Full type safety and IntelliSense
- **Modern Architecture**: App Router with server and client components
- **Performance**: Automatic code splitting and optimization
- **Testing**: Jest with Testing Library for component testing
- **Development**: Hot reload and enhanced debugging

### Frontend Architecture

- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript with strict type checking
- **Styling**: CSS modules and global styles
- **Routing**: React Router DOM (maintained for SPA behavior)
- **Testing**: Jest + Testing Library + TypeScript
- **Build**: Next.js optimized bundling

### Component Structure

```
frontend/
├── src/
│   ├── app/                 # Next.js App Router
│   │   ├── [[...slug]]/     # Catch-all route for SPA
│   │   │   ├── page.tsx     # Route handler
│   │   │   └── client.tsx   # Client-side app wrapper
│   │   └── layout.tsx       # Root layout
│   ├── components/          # React components (TypeScript)
│   │   ├── Header.tsx
│   │   ├── Login.tsx
│   │   ├── Register.tsx
│   │   ├── Dashboard.tsx
│   │   └── Credentials.tsx
│   ├── __tests__/           # Component tests
│   │   ├── Header.test.tsx
│   │   └── Login.test.tsx
│   ├── App.tsx              # Main application
│   ├── App.css             # Application styles
│   └── index.css           # Global styles
├── jest.config.js           # Test configuration
├── jest.setup.js            # Test setup
├── jest-setup.d.ts          # Jest type declarations
├── next.config.ts           # Next.js configuration
├── tsconfig.json            # TypeScript configuration
└── package.json             # Dependencies and scripts
```

### Running Tests (Frontend)

```bash
cd frontend

# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run TypeScript checks
npm run type-check
```

**Test Coverage**: Component tests verify:
- Component rendering and props
- User interactions and form submissions
- API integration mocking
- Error handling and loading states

### Test Scraper

```bash
# Set credentials in .env
echo "GIBNEY_EMAIL=your-email@example.com" >> .env
echo "GIBNEY_PASSWORD=your-password" >> .env

python test_scraper.py
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and customize the values:

```bash
cp .env.example .env
```

#### Required Variables

- **`GIBNEY_EMAIL`** - Your Gibney login email
- **`GIBNEY_PASSWORD`** - Your Gibney login password  
- **`SECRET_KEY`** - JWT signing key (generate with `openssl rand -hex 32`)
- **`ENCRYPTION_KEY`** - Credential encryption key (generate with `openssl rand -hex 32`)

#### Database Configuration

**Local Development (default):**
- Uses SQLite database (`gibster_dev.db`)
- No additional configuration needed

**Production:**
```bash
DATABASE_URL=postgresql://username:password@localhost:5432/gibster
```

#### Background Tasks

**Local Development (default):**
```bash
USE_CELERY=false  # Tasks run synchronously
```

**Production with Redis:**
```bash
USE_CELERY=true
REDIS_URL=redis://localhost:6379/0
```

#### Frontend Configuration

**Next.js Environment Variables:**
```bash
NEXT_PUBLIC_API_BASE=http://localhost:8000  # API backend URL for client-side
```

Note: Frontend now uses `NEXT_PUBLIC_` prefix instead of `REACT_APP_` for client-side environment variables.

#### Server Configuration

```bash
APP_HOST=127.0.0.1  # Server host
APP_PORT=8000       # Server port  
APP_RELOAD=true     # Auto-reload for development
```

#### Security Key Generation

Generate secure keys for production:

```bash
# Generate SECRET_KEY
openssl rand -hex 32

# Generate ENCRYPTION_KEY  
openssl rand -hex 32
```

### Complete .env.example

The project includes a comprehensive `.env.example` file with all available configuration options and detailed comments. Key sections include:

- **Gibney Credentials** - Your login information
- **Security Keys** - JWT and encryption keys
- **Database Configuration** - SQLite vs PostgreSQL options
- **Background Tasks** - Celery/Redis settings
- **Server Configuration** - Host, port, and development settings
- **Optional Production Settings** - Logging, CORS, etc.

## API Reference

- `POST /api/v1/auth/register` - Create account
- `POST /api/v1/auth/token` - Login
- `PUT /api/v1/user/credentials` - Update Gibney credentials
- `GET /api/v1/user/calendar_url` - Get calendar URL
- `GET /api/v1/user/bookings` - Get bookings
- `POST /api/v1/user/sync` - Manual sync
- `GET /calendar/{uuid}.ics` - Calendar feed

Documentation: http://localhost:8000/docs

## Deployment

### Production with Kubernetes

Gibster is designed to run on Kubernetes (K3s) with automated CI/CD through GitHub Actions.

#### Quick Deploy to K3s

```bash
# Apply development configuration
kubectl apply -k k8s/overlays/development

# For production, configure GitHub Actions secrets:
# - KUBE_CONFIG: Base64 encoded kubeconfig
# - DATABASE_URL, POSTGRES_PASSWORD, SECRET_KEY, ENCRYPTION_KEY
# Then push to main branch to trigger deployment
```

#### Manual Production Deploy

```bash
# Create secrets
kubectl create secret generic gibster-secrets \
  --from-literal=database-url="postgresql://gibster:SECURE_PASS@gibster-postgres:5432/gibster" \
  --from-literal=postgres-password="SECURE_PASS" \
  --from-literal=secret-key="$(openssl rand -hex 32)" \
  --from-literal=encryption-key="$(openssl rand -hex 32)"

# Apply production configuration
kubectl apply -k k8s/overlays/production
```

See [k8s/README.md](k8s/README.md) for detailed deployment instructions.

**Security Checklist for Production:**
- ✅ Generated secure `SECRET_KEY` and `ENCRYPTION_KEY`
- ✅ Set strong database password
- ✅ Configure TLS certificate for ingress
- ✅ Set up GitHub Actions secrets
- ✅ Configure proper resource limits

## Troubleshooting

**Scraper login fails:** Verify Gibney credentials, check site changes, ensure Playwright installed with `python -m playwright install chromium`

**"Playwright Sync API inside asyncio loop" error:** This has been fixed in the latest version. The scraper now uses Playwright's async API when called from FastAPI endpoints. If you encounter this error, ensure you have the latest code updates.

**Calendar not updating (local dev):** Manual sync available via API at `/api/v1/user/sync` or run `python -c "from backend.worker import sync_scrape_all_users; sync_scrape_all_users()"`

**Calendar not updating (Docker):** Check worker logs, verify Redis connection, restart worker

**SQLite locked errors:** Ensure database file has proper permissions, close other connections to database

**Calendar app not syncing:** Verify URL accessibility, check app refresh settings

**Database errors:** Check DATABASE_URL, ensure database accessibility

## FAQ

**How often does sync happen?** Every 2 hours automatically, plus manual sync

**Multiple Gibney accounts?** One per Gibster account currently

**Security?** Credentials encrypted with Fernet, passwords hashed with bcrypt

**Self-hosting?** Yes! Full Docker setup included

## Contributing

1. Fork and create feature branch
2. Set up development environment: `docker-compose up -d`
3. Make changes and add tests
4. Run tests: `python run_tests.py --coverage` (runs both backend + frontend)
5. Submit pull request

**Guidelines:**

- Follow PEP 8, add type hints and tests
- Maintain 80%+ test coverage
- Write descriptive commits and PR descriptions

## License

Educational purposes. Please respect Gibney's terms of service.

---

## Technical Implementation Details

### Database Schema

**users table:**

- `id` (uuid) - Primary key
- `email` (varchar) - Login email
- `password_hash` (varchar) - Hashed Gibster password
- `gibney_email` (varchar) - Encrypted Gibney username
- `gibney_pass` (varchar) - Encrypted Gibney password
- `calendar_uuid` (uuid) - Calendar feed identifier
- `created_at`, `updated_at` (timestamp)

**bookings table:**

- `id` (varchar) - Gibney booking ID
- `user_id` (uuid) - Foreign key to users
- `name` (varchar) - Booking name (e.g., "R-490015")
- `start_time`, `end_time` (timestamp)
- `studio`, `location`, `status` (varchar)
- `price` (numeric)
- `record_url` (varchar) - Link to Gibney booking
- `last_seen` (timestamp) - For cleanup

### Tech Stack Details

- **Backend:** FastAPI (Python) for high-performance API with auto-documentation
- **Frontend:** React with Vite for modern, fast UI development
- **Scraping:** Playwright for JavaScript-heavy Salesforce-based Gibney site
- **Calendar:** ics.py library for iCal generation
- **Task Queue:** Celery with Redis for background job processing
- **Database:** PostgreSQL for production, SQLite for development
- **Deployment:** Docker containers for consistent environments

### Async/Sync Implementation

The scraper system supports both async and sync execution contexts:

- **Async Version (`scrape_user_bookings`)**: Used when called from FastAPI endpoints, utilizing Playwright's async API
- **Sync Wrapper (`scrape_user_bookings_sync`)**: Uses `asyncio.run()` to execute the async version in non-async contexts (Celery tasks, background workers)
- **Context Detection**: Automatically chooses the appropriate version based on execution environment

This design prevents the "Playwright Sync API inside asyncio loop" error while maintaining compatibility with both async FastAPI endpoints and synchronous background workers.

### Security Implementation

- User passwords hashed with bcrypt
- Gibney credentials encrypted with Fernet symmetric encryption
- JWT tokens for API authentication
- HTTPS required for production
- Environment-based configuration for secrets

### Monitoring and Maintenance

```bash
# Health checks
curl http://localhost:8000/health

# View logs
docker-compose logs -f web worker

# Database backup
docker-compose exec db pg_dump -U postgres gibster > backup.sql

# Performance monitoring
docker stats
```

### SSL Setup with Caddy

```bash
# Caddyfile
yourdomain.com {
    reverse_proxy localhost:8000
}

caddy run  # Automatic SSL
```

### Development Workflow

```bash
# Full development setup
git clone <repo>
cd gibster
python setup.py  # Automated setup
# Edit .env with your settings
docker-compose up -d

# Run tests (backend + frontend)
python run_tests.py --verbose --coverage

# Frontend development
python setup.py frontend  # Setup frontend
cd frontend && npm start  # Port 3000 with API proxy
```

**⚠️ Disclaimer:** Not affiliated with Gibney Dance Center. Use responsibly.
