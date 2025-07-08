# Architecture Overview

This document provides a comprehensive overview of Gibster's system architecture, design decisions, and technical implementation details.

## System Overview

Gibster is a web application that synchronizes Gibney dance space bookings with personal calendar applications. The system uses web scraping to extract booking data and provides it via standard iCal feeds.

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Calendar  │     │   Next.js   │     │   FastAPI   │
│     Apps    │────▶│   Frontend  │────▶│   Backend   │
└─────────────┘     └─────────────┘     └─────────────┘
                            │                    │
                            ▼                    ▼
                    ┌─────────────┐     ┌─────────────┐
                    │    React    │     │ PostgreSQL/ │
                    │     SPA     │     │   SQLite    │
                    └─────────────┘     └─────────────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │  Playwright │
                                        │   Scraper   │
                                        └─────────────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │   Gibney    │
                                        │   Website   │
                                        └─────────────┘
```

## Tech Stack

### Backend

- **Framework**: FastAPI (Python 3.8+)
- **Database**: PostgreSQL (production) / SQLite (development)
- **ORM**: SQLAlchemy with async support
- **Task Queue**: Celery with Redis (production) / Synchronous (development)
- **Web Scraping**: Playwright (async API)
- **Authentication**: JWT tokens with bcrypt password hashing
- **Calendar Generation**: ics.py library

### Frontend

- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript with strict mode
- **Routing**: React Router DOM (SPA behavior)
- **Styling**: CSS modules and global styles
- **Testing**: Jest + React Testing Library
- **Build**: Next.js optimized bundling

### Infrastructure

- **Container**: Docker
- **Orchestration**: Kubernetes
- **CI/CD**: GitHub Actions
- **Monitoring**: Health checks, structured logging

## Core Components

### 1. Authentication System

**JWT-based Authentication**

- Token expiration: 30 minutes
- Secure token generation using HS256 algorithm
- Token validation on all protected endpoints

**Password Security**

- bcrypt hashing with appropriate cost factor
- No plaintext passwords stored or logged

**Credential Encryption**

- Gibney credentials encrypted with Fernet symmetric encryption
- Unique encryption key per deployment

### 2. Data Models

#### User Model

```python
class User(Base):
    id: UUID (primary key)
    email: str (unique, indexed)
    password_hash: str
    gibney_email: str (encrypted)
    gibney_password: str (encrypted)
    calendar_uuid: UUID (unique)
    is_active: bool
    last_sync_at: datetime
    created_at: datetime
    updated_at: datetime
```

#### Booking Model

```python
class Booking(Base):
    id: str (Gibney booking ID)
    user_id: UUID (foreign key)
    name: str
    start_time: datetime (indexed)
    end_time: datetime
    studio: str
    location: str
    status: str
    price: decimal
    record_url: str
    last_seen: datetime (indexed)
```

#### SyncJob Model

```python
class SyncJob(Base):
    id: UUID
    user_id: UUID
    status: str (pending|running|completed|failed)
    progress: str
    bookings_synced: int
    error_message: str
    triggered_manually: bool
    started_at: datetime
    completed_at: datetime
```

### 3. Web Scraper

**Playwright-based Scraper**

- Handles JavaScript-heavy Salesforce site
- Manages infinite scroll pagination
- Progressive wait strategies for dynamic content
- Error recovery with screenshots/HTML dumps

**Infinite Scroll Algorithm**

```
1. Load initial page content
2. Parse visible bookings
3. Scroll to bottom
4. Wait for new content or spinner
5. Repeat until no new content (4 attempts)
6. Process bookings in batches of 100
```

### 4. Calendar Integration

**iCal Feed Generation**

- Standard iCal format (RFC 5545)
- Supports both HTTPS and webcal protocols
- 2-hour cache for performance
- Filters canceled bookings

**Calendar URL Structure**

```
https://domain.com/calendar/{calendar_uuid}.ics
```

### 5. Background Processing

**Production (Celery + Redis)**

- Scheduled sync every 4 hours
- Manual sync triggers
- Job cleanup every 15 minutes
- Distributed task processing

**Development (Synchronous)**

- Direct function calls
- No external dependencies
- Simplified debugging

## Data Flow

### 1. User Registration Flow

```
User submits registration
→ Validate email uniqueness
→ Hash password with bcrypt
→ Generate calendar UUID
→ Create user record
→ Return JWT token
```

### 2. Booking Sync Flow

```
User triggers sync (manual/automatic)
→ Validate Gibney credentials
→ Create sync job record
→ Launch Playwright browser
→ Login to Gibney website
→ Navigate to bookings page
→ Handle infinite scroll
→ Extract booking data
→ Update database (bulk operations)
→ Update sync job status
→ Notify user of completion
```

### 3. Calendar Feed Flow

```
Calendar app requests feed
→ Extract UUID from URL
→ Find user by calendar UUID
→ Fetch non-canceled bookings
→ Generate iCal events
→ Cache for 2 hours
→ Return iCal formatted data
```

## Security Architecture

### Authentication & Authorization

- Bearer token authentication
- Token validation middleware
- User context injection
- Protected endpoint decorators

### Data Protection

- Fernet encryption for credentials
- bcrypt for password hashing
- Parameterized SQL queries
- Input validation with Pydantic

### Network Security

- HTTPS enforcement in production
- CORS configuration
- Request ID tracking
- Rate limiting (planned)

## Performance Optimizations

### Database

- Connection pooling
- Indexed fields for common queries
- Bulk insert/update operations
- Query execution monitoring

### Caching

- 2-hour calendar feed cache
- Browser static asset caching
- ETags for cache validation

### Scraping

- Batch processing (100 bookings)
- Hash-based change detection
- Concurrent browser instances limit
- Progressive wait strategies

## Scalability Considerations

### Horizontal Scaling

- Stateless API design
- Database connection pooling
- Distributed task processing
- Load balancer ready

### Resource Management

- Controlled browser instances
- Automatic cleanup jobs
- Connection limits
- Memory-efficient batch processing

## Monitoring & Observability

### Logging

- Structured JSON logging
- Request/response tracking
- Unique request IDs
- Error context capture

### Health Checks

- Database connectivity
- Service status
- Kubernetes probes
- Dependency checks

### Metrics

- API response times
- Database query duration
- Sync job statistics
- Error rates

## Design Decisions

### Why FastAPI?

- High performance async support
- Automatic API documentation
- Built-in validation with Pydantic
- Modern Python features

### Why Playwright?

- Handles JavaScript-heavy sites
- Reliable browser automation
- Async API support
- Good error recovery

### Why Next.js?

- Server-side rendering options
- Optimized production builds
- TypeScript support
- Modern React features

### Why PostgreSQL/SQLite?

- PostgreSQL for production reliability
- SQLite for zero-config development
- SQLAlchemy abstraction layer
- Easy migration path

## API Design

### RESTful Endpoints

```
POST   /api/v1/auth/register      - User registration
POST   /api/v1/auth/token         - User login
GET    /api/v1/user/profile       - Get user info
PUT    /api/v1/user/credentials   - Update Gibney credentials
GET    /api/v1/user/bookings      - List bookings
POST   /api/v1/user/sync          - Trigger sync
GET    /api/v1/user/sync/status   - Get sync status
GET    /calendar/{uuid}.ics       - Calendar feed
```

### Response Format

```json
{
  "status": "success|error",
  "data": {...},
  "message": "Human readable message",
  "error": "Error details if applicable"
}
```

## Database Schema

See [Database Models](#2-data-models) section above for detailed schema.

### Key Relationships

- User → Bookings (one-to-many)
- User → SyncJobs (one-to-many)
- SyncJob → SyncJobLogs (one-to-many)

### Indexes

- `users.email` - Unique constraint
- `users.calendar_uuid` - Unique constraint
- `bookings.user_id` - Foreign key index
- `bookings.start_time` - Performance index
- `bookings.last_seen` - Cleanup operations

## Deployment Architecture

### Development

- Single process
- SQLite database
- Synchronous tasks
- Hot reload enabled

### Production

- Kubernetes deployment
- PostgreSQL StatefulSet
- Redis for Celery
- Horizontal pod autoscaling
- Ingress with TLS

### CI/CD Pipeline

```
Push to main
→ Run tests
→ Build Docker images
→ Push to registry
→ Update Kubernetes manifests
→ Apply to cluster
→ Verify deployment
```

## Future Considerations

### Planned Improvements

- Rate limiting implementation
- Refresh token mechanism
- Two-factor authentication
- Webhook notifications
- Mobile app API

### Scalability Path

- Read replicas for database
- CDN for static assets
- Caching layer (Redis)
- Message queue for events
- Microservices architecture
