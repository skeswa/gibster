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

### Using Docker (Recommended)

```bash
git clone <your-repo-url>
cd gibster
python setup.py  # Creates .env and installs dependencies
# Edit .env with your secure keys
docker-compose up -d
```

Access at http://localhost:8000

### Manual Setup

```bash
python setup.py  # Automated setup: installs dependencies, creates .env, sets up Playwright
# Edit .env file with your settings

# Start services in separate terminals:
redis-server
python run_server.py
python run_worker.py
```

The setup script automatically:
- Creates `.env` file from template
- Installs Python dependencies
- Installs Playwright browser
- Provides next steps guidance

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

```bash
# Run all tests with coverage
python run_tests.py --coverage

# Run specific test types
python run_tests.py --type unit
python run_tests.py --type integration

# Using pytest directly
pytest -v --cov=app
```

### Frontend Development

```bash
cd frontend
npm install
npm start
```

Frontend available at http://localhost:3000 with API proxy to backend.

### Test Scraper

```bash
# Set credentials in .env
echo "GIBNEY_EMAIL=your-email@example.com" >> .env
echo "GIBNEY_PASSWORD=your-password" >> .env

python test_scraper.py
```

## Configuration

### Environment Variables

**Required:**
- `SECRET_KEY` - JWT signing key (generate with `openssl rand -hex 32`)
- `ENCRYPTION_KEY` - Credential encryption key

**Optional:**
- `DATABASE_URL` - Database connection (default: SQLite)
- `REDIS_URL` - Redis connection (default: `redis://localhost:6379/0`)

### Example .env

```bash
SECRET_KEY=your-very-secure-secret-key-here
ENCRYPTION_KEY=your-encryption-key-here
DATABASE_URL=postgresql://user:password@localhost:5432/gibster
REDIS_URL=redis://localhost:6379/0
```

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

### Production with Docker

```bash
# Create production override
cat > docker-compose.prod.yml << 'EOF'
version: '3.8'
services:
  web:
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/gibster
      - SECRET_KEY=${SECRET_KEY}
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
    ports:
      - "127.0.0.1:8000:8000"
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=gibster
      - POSTGRES_USER=gibster
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
volumes:
  postgres_data:
EOF

docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Cloud Platforms

**Fly.io:**
```bash
flyctl launch
flyctl secrets set SECRET_KEY=your-key ENCRYPTION_KEY=your-key
flyctl deploy
```

**Heroku:**
```bash
heroku create your-app
heroku addons:create heroku-postgresql:mini heroku-redis:mini
heroku config:set SECRET_KEY=your-key ENCRYPTION_KEY=your-key
git push heroku main
```

## Troubleshooting

**Scraper login fails:** Verify Gibney credentials, check site changes, ensure Playwright installed

**Calendar not updating:** Check worker logs, verify Redis connection, restart worker

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
4. Run tests: `python run_tests.py --coverage`
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

# Run tests
python run_tests.py --verbose --coverage

# Frontend development
python setup.py frontend  # Setup frontend
cd frontend && npm start  # Port 3000 with API proxy
```

**⚠️ Disclaimer:** Not affiliated with Gibney Dance Center. Use responsibly.
