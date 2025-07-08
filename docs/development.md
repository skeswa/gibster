# Development Guide

This guide covers the complete development setup and workflow for Gibster.

## Development Environment Setup

### Prerequisites

- Python 3.8 or higher
- Node.js 18 or higher
- Git
- Chrome/Chromium browser (for Playwright)

### Initial Setup

1. **Clone and Setup**

   ```bash
   git clone <your-repo-url>
   cd gibster
   python scripts/dev_setup.py
   ```

2. **Activate Virtual Environment**

   ```bash
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Configure Environment Variables**

   Edit `backend/.env`:

   ```bash
   # Gibney credentials (required for testing scraper)
   GIBNEY_EMAIL=your-email@example.com
   GIBNEY_PASSWORD=your-password

   # Security keys (generate for production)
   SECRET_KEY=your-secret-key-here
   ENCRYPTION_KEY=your-encryption-key-here
   ```

## Development Commands

### Backend Development

```bash
# Start development server
python scripts/run_server.py

# Run database migrations
cd backend && alembic upgrade head

# Create new migration
cd backend && alembic revision --autogenerate -m "description"

# Format code
black backend/
isort backend/

# Type checking
mypy backend --ignore-missing-imports

# Run backend tests only
python scripts/run_tests.py --backend-only
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start development server (port 3000)
npm run dev

# Build for production
npm run build

# Run tests
npm test

# Run tests in watch mode
npm run test:watch

# Lint code
npm run lint

# Type checking
npm run type-check

# Format code
npm run format
```

### Full Stack Development

Run both frontend and backend simultaneously:

```bash
# Terminal 1: Backend
source venv/bin/activate
python scripts/run_server.py

# Terminal 2: Frontend
cd frontend
npm run dev
```

Access:

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Code Style and Standards

### Python (Backend)

- **Style Guide**: PEP 8
- **Formatter**: Black (line length: 88)
- **Import Sorting**: isort
- **Type Hints**: Required for all functions
- **Docstrings**: Google style

Example:

```python
from typing import Optional

def get_user_by_email(email: str, db: Session) -> Optional[User]:
    """Retrieve a user by their email address.

    Args:
        email: The user's email address
        db: Database session

    Returns:
        User object if found, None otherwise
    """
    return db.query(User).filter(User.email == email).first()
```

### TypeScript/JavaScript (Frontend)

- **Language**: TypeScript with strict mode
- **Style**: ESLint with React hooks rules
- **Formatter**: Prettier
- **Components**: Functional components with hooks

Example:

```typescript
interface DashboardProps {
  user: User;
  onSync: () => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ user, onSync }) => {
  const [loading, setLoading] = useState(false);

  // Component logic
};
```

## Project Structure

```
gibster/
├── backend/
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── core/        # Core utilities
│   │   ├── crud/        # Database operations
│   │   ├── models/      # SQLAlchemy models
│   │   └── schemas/     # Pydantic schemas
│   ├── tests/           # Backend tests
│   ├── alembic/         # Database migrations
│   └── requirements.txt # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── app/         # Next.js app directory
│   │   ├── components/  # React components
│   │   ├── lib/         # Utilities and API client
│   │   └── __tests__/   # Frontend tests
│   └── package.json     # Node dependencies
├── scripts/             # Development scripts
└── docs/               # Documentation
```

## Database Management

### Local Development Database

Development uses SQLite by default:

- Location: `backend/gibster_dev.db`
- Auto-created on first run

### Working with Migrations

```bash
cd backend

# View current migration status
alembic current

# Upgrade to latest
alembic upgrade head

# Downgrade one revision
alembic downgrade -1

# Create new migration
alembic revision --autogenerate -m "Add new field to user"
```

### Database Schema

See the [Architecture Guide](architecture.md#database-schema) for detailed schema information.

## API Development

### Adding New Endpoints

1. **Create Schema** (`backend/app/schemas/`):

   ```python
   class BookingUpdate(BaseModel):
       name: Optional[str] = None
       status: Optional[str] = None
   ```

2. **Add CRUD Operation** (`backend/app/crud/`):

   ```python
   def update_booking(db: Session, booking_id: str, update_data: dict):
       # Implementation
   ```

3. **Create Endpoint** (`backend/app/api/v1/`):
   ```python
   @router.put("/bookings/{booking_id}")
   def update_booking(
       booking_id: str,
       booking_update: BookingUpdate,
       db: Session = Depends(get_db),
       current_user: User = Depends(get_current_user)
   ):
       # Implementation
   ```

### API Documentation

FastAPI automatically generates documentation:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Frontend Development

### Component Development

1. **Create Component** (`frontend/src/components/`):

   ```typescript
   export const MyComponent: React.FC<Props> = ({ prop1, prop2 }) => {
     // Component logic
   };
   ```

2. **Add Tests** (`frontend/src/__tests__/`):

   ```typescript
   describe("MyComponent", () => {
     it("renders correctly", () => {
       render(<MyComponent prop1="test" />);
       expect(screen.getByText("test")).toBeInTheDocument();
     });
   });
   ```

3. **Use in Application**:
   ```typescript
   import { MyComponent } from "./components/MyComponent";
   ```

### State Management

The application uses React hooks for state management:

- `useState` for local component state
- `useContext` for global state (authentication)
- `useEffect` for side effects

### API Integration

API calls are made using the fetch API with proper error handling:

```typescript
const syncBookings = async () => {
  try {
    const response = await fetch("/api/v1/user/sync", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error("Sync failed");
    }

    const data = await response.json();
    // Handle success
  } catch (error) {
    // Handle error
  }
};
```

## Testing

See the [Testing Guide](testing.md) for comprehensive testing documentation.

## Debugging

### Backend Debugging

1. **Enable Debug Logging**:

   ```bash
   export APP_DEBUG=true
   export DATABASE_DEBUG=true
   ```

2. **Use Python Debugger**:

   ```python
   import pdb; pdb.set_trace()
   ```

3. **View SQL Queries**:
   Set `DATABASE_DEBUG=true` to see all SQL queries

### Frontend Debugging

1. **React Developer Tools**: Install browser extension
2. **Console Logging**: Use `console.log` for debugging
3. **Network Tab**: Monitor API calls in browser DevTools

### Scraper Debugging

When scraper fails, debug files are created:

- `debug_*.png` - Screenshot at failure
- `debug_*.html` - HTML content

Test scraper manually:

```bash
python scripts/test_scraper.py
```

## Common Development Tasks

### Update Dependencies

**Python**:

```bash
pip install --upgrade package-name
pip freeze > backend/requirements.txt
```

**JavaScript**:

```bash
cd frontend
npm update
npm audit fix
```

### Run Linters and Formatters

```bash
# Backend
black backend/
isort backend/
mypy backend --ignore-missing-imports

# Frontend
cd frontend
npm run lint
npm run format
```

### Database Reset

```bash
# Delete database
rm backend/gibster_dev.db

# Recreate with migrations
cd backend
alembic upgrade head
```

## Environment Variables Reference

### Backend (.env)

```bash
# Required
SECRET_KEY=your-secret-key
ENCRYPTION_KEY=your-encryption-key

# Optional
DATABASE_URL=sqlite:///./gibster_dev.db
USE_CELERY=false
APP_HOST=127.0.0.1
APP_PORT=8000
APP_RELOAD=true
```

### Frontend (.env.local)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Troubleshooting Development Issues

### Common Issues

1. **Import Errors**: Ensure virtual environment is activated
2. **Database Locked**: Close other connections to SQLite
3. **Port Already in Use**: Kill existing processes or change port
4. **Playwright Issues**: Run `python -m playwright install chromium`

### Getting Help

- Check existing [GitHub Issues](https://github.com/your-repo/issues)
- Review [Architecture Documentation](architecture.md)
- See [Testing Guide](testing.md) for test-related issues
