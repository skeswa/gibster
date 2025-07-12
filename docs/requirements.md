# Gibster Requirements Document

## Overview

Gibster is a web application designed to synchronize Gibney dance space bookings with personal calendar applications. The system automatically scrapes booking information from the Gibney website and generates subscribable calendar feeds, eliminating the manual effort required for dancers to maintain their schedules across multiple platforms.

## Functional Requirements

### 1. User Account Management

#### 1.1 User Registration

- **FR-1.1.1**: The system shall allow new users to register using an email address and password
- **FR-1.1.2**: The system shall validate email format and uniqueness during registration
- **FR-1.1.3**: The system shall generate a unique calendar UUID for each new user
- **FR-1.1.4**: The system shall hash passwords using bcrypt before storage

#### 1.2 User Authentication

- **FR-1.2.1**: The system shall authenticate users via email and password
- **FR-1.2.2**: The system shall issue JWT tokens valid for 30 minutes upon successful authentication
- **FR-1.2.3**: The system shall support OAuth2 password flow for token acquisition
- **FR-1.2.4**: The system shall validate JWT tokens on all protected endpoints

#### 1.3 User Profile Management

- **FR-1.3.1**: The system shall allow authenticated users to view their profile information
- **FR-1.3.2**: The system shall display user email, calendar UUID, and account creation date

### 2. Gibney Credential Management

#### 2.1 Credential Storage

- **FR-2.1.1**: The system shall allow users to store their Gibney website credentials
- **FR-2.1.2**: The system shall encrypt credentials using Fernet symmetric encryption before storage
- **FR-2.1.3**: The system shall pre-populate the email field when updating credentials
- **FR-2.1.4**: The system shall clear password fields after successful update

#### 2.2 Credential Retrieval

- **FR-2.2.1**: The system shall decrypt and retrieve stored Gibney email for display
- **FR-2.2.2**: The system shall never expose decrypted passwords to the user interface

### 3. Booking Synchronization

#### 3.1 Manual Synchronization

- **FR-3.1.1**: The system shall allow users to manually trigger booking synchronization
- **FR-3.1.2**: The system shall prevent multiple concurrent synchronizations for the same user
- **FR-3.1.3**: The system shall validate Gibney credentials before starting synchronization
- **FR-3.1.4**: The system shall create trackable sync jobs with real-time progress updates

#### 3.2 Automatic Synchronization

- **FR-3.2.1**: The system shall automatically synchronize all users' bookings every 4 hours
- **FR-3.2.2**: The system shall run scheduled sync jobs when Celery is enabled
- **FR-3.2.3**: The system shall track whether sync jobs were triggered manually or automatically

#### 3.3 Sync Status Tracking

- **FR-3.3.1**: The system shall display current sync job status (pending, running, completed, failed)
- **FR-3.3.2**: The system shall show progress messages during synchronization
- **FR-3.3.3**: The system shall track the number of bookings synchronized
- **FR-3.3.4**: The system shall store and display error messages for failed syncs

#### 3.4 Sync History

- **FR-3.4.1**: The system shall maintain a history of all sync jobs
- **FR-3.4.2**: The system shall display sync history with pagination (default 10 items)
- **FR-3.4.3**: The system shall show the most recent sync jobs first
- **FR-3.4.4**: The system shall allow viewing of last 3 sync jobs on the dashboard

#### 3.5 Sync Logging

- **FR-3.5.1**: The system shall log detailed sync operations with timestamps
- **FR-3.5.2**: The system shall support log level filtering (INFO, WARNING, ERROR, DEBUG)
- **FR-3.5.3**: The system shall store structured log details for analysis
- **FR-3.5.4**: The system shall provide paginated log viewing with 20 entries per page

### 4. Booking Data Management

#### 4.1 Booking Storage

- **FR-4.1.1**: The system shall store all scraped bookings with complete details
- **FR-4.1.2**: The system shall track booking ID, name, dates, studio, location, status, and price
- **FR-4.1.3**: The system shall store direct links to original Gibney booking pages
- **FR-4.1.4**: The system shall update existing bookings when changes are detected

#### 4.2 Booking Display

- **FR-4.2.1**: The system shall display all user bookings in a tabular format
- **FR-4.2.2**: The system shall show booking count to users
- **FR-4.2.3**: The system shall provide external links to view bookings on Gibney website
- **FR-4.2.4**: The system shall automatically refresh booking display after sync completion

#### 4.3 Booking Change Detection

- **FR-4.3.1**: The system shall generate SHA256 hashes of booking data for change detection
- **FR-4.3.2**: The system shall only update bookings when content changes are detected
- **FR-4.3.3**: The system shall track last seen timestamp for each booking

### 5. Calendar Integration

#### 5.1 Calendar Feed Generation

- **FR-5.1.1**: The system shall generate iCal format calendar feeds for each user
- **FR-5.1.2**: The system shall include booking name, time, location, and details in calendar events
- **FR-5.1.3**: The system shall filter out canceled bookings from calendar feeds
- **FR-5.1.4**: The system shall support both HTTPS and webcal protocols
- **FR-5.1.5**: The system shall personalize calendar names with format "Gibster - user@email.com"
- **FR-5.1.6**: The system shall include personalized metadata (X-WR-CALNAME, X-WR-CALDESC) in calendar content

#### 5.2 Calendar URL Management

- **FR-5.2.1**: The system shall provide unique calendar URLs using user's calendar UUID
- **FR-5.2.2**: The system shall allow calendar access without authentication via UUID
- **FR-5.2.3**: The system shall support copy-to-clipboard functionality for calendar URLs
- **FR-5.2.4**: The system shall proxy calendar URLs through the frontend domain
- **FR-5.2.5**: The system shall generate personalized filenames for downloaded calendars (gibster-user-at-email.com.ics)

#### 5.3 Calendar Application Support

- **FR-5.3.1**: The system shall provide one-click subscription for Google Calendar
- **FR-5.3.2**: The system shall provide one-click subscription for Apple Calendar
- **FR-5.3.3**: The system shall provide one-click subscription for Outlook with personalized calendar name
- **FR-5.3.4**: The system shall cache calendar feeds for 2 hours for performance

### 6. Web Scraping

#### 6.1 Gibney Website Authentication

- **FR-6.1.1**: The scraper shall authenticate with Gibney website using stored credentials
- **FR-6.1.2**: The scraper shall handle multiple login form variations
- **FR-6.1.3**: The scraper shall verify successful login before proceeding
- **FR-6.1.4**: The scraper shall navigate to the rentals page after login

#### 6.2 Booking Data Extraction

- **FR-6.2.1**: The scraper shall extract all visible bookings from the rentals table
- **FR-6.2.2**: The scraper shall parse booking dates in multiple formats
- **FR-6.2.3**: The scraper shall extract booking ID from rental URLs
- **FR-6.2.4**: The scraper shall handle missing or malformed data gracefully

#### 6.3 Infinite Scroll Handling

- **FR-6.3.1**: The scraper shall automatically scroll to load all bookings
- **FR-6.3.2**: The scraper shall detect and wait for loading spinners
- **FR-6.3.3**: The scraper shall retry scrolling up to 4 times when no new content appears
- **FR-6.3.4**: The scraper shall process bookings in batches of 100

#### 6.4 Error Handling

- **FR-6.4.1**: The scraper shall capture screenshots on failure for debugging
- **FR-6.4.2**: The scraper shall save page HTML on failure for analysis
- **FR-6.4.3**: The scraper shall implement retry logic for transient failures
- **FR-6.4.4**: The scraper shall provide detailed error messages for troubleshooting

### 7. Administrative Functions

#### 7.1 Sync Job Cleanup

- **FR-7.1.1**: The system shall automatically clean up old sync jobs every 15 minutes
- **FR-7.1.2**: The system shall mark stale running jobs as failed after timeout
- **FR-7.1.3**: The system shall delete completed jobs older than 30 days
- **FR-7.1.4**: The system shall provide manual cleanup endpoint for administrators

### 8. User Interface

#### 8.1 Public Pages

- **FR-8.1.1**: The system shall provide a landing page with feature overview
- **FR-8.1.2**: The system shall display privacy policy and terms of service
- **FR-8.1.3**: The system shall show how the service works in 3 steps
- **FR-8.1.4**: The system shall include customer testimonials

#### 8.2 Authentication Interface

- **FR-8.2.1**: The system shall provide login and registration forms
- **FR-8.2.2**: The system shall display validation errors inline
- **FR-8.2.3**: The system shall show loading states during authentication
- **FR-8.2.4**: The system shall redirect to dashboard after successful login

#### 8.3 Dashboard Interface

- **FR-8.3.1**: The system shall display calendar subscription options prominently
- **FR-8.3.2**: The system shall show sync status and controls
- **FR-8.3.3**: The system shall display booking table with all details
- **FR-8.3.4**: The system shall auto-refresh data after sync completion

#### 8.4 Settings Interface

- **FR-8.4.1**: The system shall provide credential update form
- **FR-8.4.2**: The system shall explain credential security measures
- **FR-8.4.3**: The system shall show success/error messages for updates

#### 8.5 Theme Support

- **FR-8.5.1**: The system shall support light, dark, and system theme modes
- **FR-8.5.2**: The system shall persist theme selection across sessions
- **FR-8.5.3**: The system shall provide theme toggle in navigation
- **FR-8.5.4**: The system shall prevent flash of unstyled content on load

## Non-Functional Requirements

### 1. Security Requirements

#### 1.1 Authentication Security

- **NFR-1.1.1**: The system shall use bcrypt with appropriate cost factor for password hashing
- **NFR-1.1.2**: The system shall generate cryptographically secure JWT tokens
- **NFR-1.1.3**: The system shall enforce HTTPS for all production communications
- **NFR-1.1.4**: The system shall validate all input to prevent injection attacks

#### 1.2 Data Protection

- **NFR-1.2.1**: The system shall encrypt all Gibney credentials at rest using Fernet
- **NFR-1.2.2**: The system shall never log or expose sensitive credentials
- **NFR-1.2.3**: The system shall use parameterized queries to prevent SQL injection
- **NFR-1.2.4**: The system shall implement proper session management

#### 1.3 Access Control

- **NFR-1.3.1**: The system shall enforce authentication on all user-specific endpoints
- **NFR-1.3.2**: The system shall prevent users from accessing other users' data
- **NFR-1.3.3**: The system shall use UUIDs for public calendar URLs to prevent enumeration
- **NFR-1.3.4**: The system shall implement proper CORS policies for production

### 2. Performance Requirements

#### 2.1 Response Time

- **NFR-2.1.1**: The system shall respond to API requests within 1 second under normal load
- **NFR-2.1.2**: The system shall generate calendar feeds within 2 seconds
- **NFR-2.1.3**: The system shall display sync progress updates in real-time
- **NFR-2.1.4**: The system shall load dashboard data within 3 seconds

#### 2.2 Scalability

- **NFR-2.2.1**: The system shall support concurrent sync operations for multiple users
- **NFR-2.2.2**: The system shall handle at least 1000 active users
- **NFR-2.2.3**: The system shall process bookings in batches to manage memory usage
- **NFR-2.2.4**: The system shall implement database connection pooling

#### 2.3 Caching

- **NFR-2.3.1**: The system shall cache calendar feeds for 2 hours
- **NFR-2.3.2**: The system shall implement browser caching for static assets
- **NFR-2.3.3**: The system shall use ETags for efficient cache validation

### 3. Reliability Requirements

#### 3.1 Availability

- **NFR-3.1.1**: The system shall maintain 99% uptime during business hours
- **NFR-3.1.2**: The system shall handle Gibney website changes gracefully
- **NFR-3.1.3**: The system shall continue serving cached calendars during sync failures
- **NFR-3.1.4**: The system shall implement health checks for monitoring

#### 3.2 Error Recovery

- **NFR-3.2.1**: The system shall retry failed sync operations with exponential backoff
- **NFR-3.2.2**: The system shall recover from database connection failures
- **NFR-3.2.3**: The system shall handle browser automation crashes gracefully
- **NFR-3.2.4**: The system shall clean up stale sync jobs automatically

#### 3.3 Data Integrity

- **NFR-3.3.1**: The system shall maintain referential integrity in the database
- **NFR-3.3.2**: The system shall use transactions for critical operations
- **NFR-3.3.3**: The system shall validate all data before storage
- **NFR-3.3.4**: The system shall handle timezone conversions correctly

### 4. Usability Requirements

#### 4.1 User Experience

- **NFR-4.1.1**: The system shall provide clear feedback for all user actions
- **NFR-4.1.2**: The system shall display helpful error messages
- **NFR-4.1.3**: The system shall maintain consistent UI patterns throughout
- **NFR-4.1.4**: The system shall support mobile-responsive layouts

#### 4.2 Accessibility

- **NFR-4.2.1**: The system shall support keyboard navigation
- **NFR-4.2.2**: The system shall provide appropriate ARIA labels
- **NFR-4.2.3**: The system shall maintain sufficient color contrast ratios
- **NFR-4.2.4**: The system shall support screen readers

#### 4.3 Documentation

- **NFR-4.3.1**: The system shall provide clear setup instructions
- **NFR-4.3.2**: The system shall explain how calendar synchronization works
- **NFR-4.3.3**: The system shall document security measures for user trust
- **NFR-4.3.4**: The system shall include troubleshooting guides

### 5. Maintainability Requirements

#### 5.1 Code Quality

- **NFR-5.1.1**: The system shall follow PEP 8 style guidelines for Python code
- **NFR-5.1.2**: The system shall use TypeScript for type safety in frontend
- **NFR-5.1.3**: The system shall maintain test coverage above 80%
- **NFR-5.1.4**: The system shall use linting and formatting tools

#### 5.2 Monitoring

- **NFR-5.2.1**: The system shall log all API requests with timing information
- **NFR-5.2.2**: The system shall track slow database queries
- **NFR-5.2.3**: The system shall provide detailed sync operation logs
- **NFR-5.2.4**: The system shall generate unique request IDs for tracing

#### 5.3 Deployment

- **NFR-5.3.1**: The system shall support containerized deployment
- **NFR-5.3.2**: The system shall use CI/CD for automated testing and deployment
- **NFR-5.3.3**: The system shall support zero-downtime deployments
- **NFR-5.3.4**: The system shall maintain separate development and production environments

### 6. Compatibility Requirements

#### 6.1 Browser Support

- **NFR-6.1.1**: The system shall support Chrome, Firefox, Safari, and Edge browsers
- **NFR-6.1.2**: The system shall work on browsers released within the last 2 years
- **NFR-6.1.3**: The system shall provide graceful degradation for older browsers

#### 6.2 Calendar Application Support

- **NFR-6.2.1**: The system shall generate iCal feeds compatible with major calendar apps
- **NFR-6.2.2**: The system shall support both HTTP and webcal protocols
- **NFR-6.2.3**: The system shall handle calendar client quirks appropriately

#### 6.3 Platform Support

- **NFR-6.3.1**: The system shall run on Linux-based production environments
- **NFR-6.3.2**: The system shall support development on macOS and Windows
- **NFR-6.3.3**: The system shall use platform-agnostic path handling

### 7. Operational Requirements

#### 7.1 Resource Management

- **NFR-7.1.1**: The system shall limit concurrent browser instances for scraping
- **NFR-7.1.2**: The system shall implement request rate limiting in production
- **NFR-7.1.3**: The system shall clean up temporary files automatically
- **NFR-7.1.4**: The system shall manage database connections efficiently

#### 7.2 Background Processing

- **NFR-7.2.1**: The system shall use Celery for production background tasks
- **NFR-7.2.2**: The system shall support synchronous processing for development
- **NFR-7.2.3**: The system shall prevent duplicate scheduled tasks
- **NFR-7.2.4**: The system shall handle worker failures gracefully

#### 7.3 Configuration Management

- **NFR-7.3.1**: The system shall support environment-based configuration
- **NFR-7.3.2**: The system shall validate all configuration on startup
- **NFR-7.3.3**: The system shall support secrets management for sensitive data
- **NFR-7.3.4**: The system shall provide sensible defaults for development

## Technical Constraints

### 1. External Dependencies

- **TC-1.1**: The system depends on Gibney website structure remaining parseable
- **TC-1.2**: The system requires Playwright-compatible browser for scraping
- **TC-1.3**: The system requires PostgreSQL for production database
- **TC-1.4**: The system requires Redis for production background tasks

### 2. Infrastructure Requirements

- **TC-2.1**: Production deployment requires Kubernetes cluster
- **TC-2.2**: The system requires persistent volume for database storage
- **TC-2.3**: The system requires ingress controller for HTTPS
- **TC-2.4**: The system requires container registry for images

### 3. Development Requirements

- **TC-3.1**: Backend development requires Python 3.8 or higher
- **TC-3.2**: Frontend development requires Node.js 18 or higher
- **TC-3.3**: The system uses specific package versions for stability
- **TC-3.4**: Development requires Chrome/Chromium for scraper testing
