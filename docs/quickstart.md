# Quick Start Guide

This guide will help you get Gibster up and running quickly on your local machine.

## Prerequisites

- Python 3.8 or higher
- Node.js 18 or higher
- Git

## Installation

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd gibster
```

### 2. Run Automated Setup

```bash
python scripts/dev_setup.py
```

This automated setup script will:

- Create a Python virtual environment
- Install all Python dependencies
- Install Playwright browser for web scraping
- Create SQLite development database
- Create `.env` file from template
- Check for optional services (Redis)

### 3. Configure Environment

After setup, edit the generated `.env` file in the `backend/` directory:

```bash
# Edit backend/.env
GIBNEY_EMAIL=your-email@example.com
GIBNEY_PASSWORD=your-password

# Generate secure keys for production
SECRET_KEY=<generate with: openssl rand -hex 32>
ENCRYPTION_KEY=<generate with: openssl rand -hex 32>
```

### 4. Start the Development Server

```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Start the server
python scripts/run_server.py
```

The application will be available at http://localhost:8000

## Using Gibster

### 1. Create an Account

1. Navigate to http://localhost:8000
2. Click "Register"
3. Enter your email and create a password

### 2. Add Gibney Credentials

1. Log in to your Gibster account
2. Go to Settings/Credentials
3. Enter your Gibney website login credentials
4. Click "Update Credentials"

### 3. Subscribe to Your Calendar

From the dashboard, you have several options:

#### Quick Add (One-Click)

- **Google Calendar**: Click "Add to Google Calendar" button
- **Apple Calendar**: Click "Add to Apple Calendar" button
- **Outlook**: Click "Add to Outlook" button

#### Manual Subscription

Copy your calendar URL and add it to your calendar app:

**Google Calendar:**

1. Open Google Calendar → Settings → Add calendar → From URL
2. Paste your calendar URL
3. Click "Add calendar"

**Apple Calendar:**

1. File → New Calendar Subscription
2. Paste your calendar URL
3. Choose update frequency (recommended: every 2 hours)

**Outlook.com:**

1. Calendar → Add calendar → Subscribe from web
2. Paste your calendar URL
3. Name it "Gibney Bookings"

### 4. Sync Your Bookings

- **Automatic**: Bookings sync every 2 hours automatically
- **Manual**: Click "Sync Now" on the dashboard for immediate updates

## Next Steps

- View the [Development Guide](development.md) for detailed development setup
- See [Architecture Overview](architecture.md) to understand the system design
- Check [Testing Guide](testing.md) for running tests
- Read [Deployment Guide](deployment.md) for production deployment

## Troubleshooting

### Common Issues

**Scraper login fails**

- Verify your Gibney credentials are correct
- Ensure Playwright is installed: `python -m playwright install chromium`

**Calendar not updating**

- Try manual sync from the dashboard
- Check your calendar app's refresh settings

**Database errors**

- Ensure the SQLite database has proper permissions
- Try deleting `backend/gibster_dev.db` and rerunning migrations

For more troubleshooting tips, see the main [README](../README.md#troubleshooting).
