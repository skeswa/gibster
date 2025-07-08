# Testing Guide

This guide covers the testing strategy, tools, and practices for the Gibster project.

## Overview

Gibster uses a comprehensive testing approach with:

- **Backend**: Python tests with pytest
- **Frontend**: React component tests with Jest
- **Type Checking**: mypy (Python) and TypeScript compiler
- **End-to-End**: Playwright-based scraper tests

## Quick Start

### Run All Tests

```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run all tests with type checking and coverage
python scripts/run_tests.py --coverage

# Run without type checking
python scripts/run_tests.py --skip-type-check

# Run type checking only
python scripts/run_tests.py --type-check-only
```

### Test Options

```bash
# Backend only
python scripts/run_tests.py --backend-only

# Frontend only
python scripts/run_tests.py --frontend-only

# Specific test types (backend)
python scripts/run_tests.py --backend-only --type unit
python scripts/run_tests.py --backend-only --type integration

# Verbose output
python scripts/run_tests.py --verbose

# End-to-end tests (requires Gibney credentials)
python scripts/run_tests.py --e2e
```

## Backend Testing

### Test Structure

```
backend/tests/
├── conftest.py          # Shared fixtures
├── test_auth.py         # Authentication tests
├── test_models.py       # Database model tests
├── test_api_integration.py  # API endpoint tests
├── test_scraper.py      # Scraper unit tests
├── test_scraper_e2e.py  # End-to-end scraper tests
└── test_sync.py         # Sync job tests
```

### Test Categories

Tests are marked with pytest markers:

- `@pytest.mark.unit` - Fast unit tests without external dependencies
- `@pytest.mark.integration` - Tests that use database or other services

### Running Backend Tests

```bash
# Run all backend tests with type checking
python scripts/run_tests.py --backend-only

# Run only unit tests
pytest -v -m unit backend/tests/

# Run only integration tests
pytest -v -m integration backend/tests/

# Run specific test file
pytest -v backend/tests/test_auth.py

# Run with coverage
pytest -v --cov=backend backend/tests/

# Run specific test function
pytest -v backend/tests/test_auth.py::test_password_hashing
```

### Backend Test Examples

#### Unit Test Example

```python
@pytest.mark.unit
def test_password_hashing():
    """Test password hashing and verification"""
    password = "testpassword123"
    hashed = get_password_hash(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False
```

#### Integration Test Example

```python
@pytest.mark.integration
def test_user_registration(client, test_db):
    """Test user registration endpoint"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "password123"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "access_token" in data
```

### Database Testing

Tests use a temporary SQLite database that's created and destroyed for each test:

```python
@pytest.fixture
def test_db():
    """Create temporary test database"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
        db_path = tmp_file.name

    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(bind=engine)

    yield SessionLocal()

    os.unlink(db_path)
```

### Type Checking (Backend)

```bash
# Run mypy type checking
mypy backend --ignore-missing-imports

# Type checking is included by default in test runner
python scripts/run_tests.py --backend-only

# Skip type checking
python scripts/run_tests.py --backend-only --skip-type-check
```

## Frontend Testing

### Test Structure

```
frontend/src/__tests__/
├── Header.test.tsx      # Header component tests
├── Login.test.tsx       # Login component tests
└── Dashboard.test.tsx   # Dashboard component tests
```

### Running Frontend Tests

```bash
cd frontend

# Run all tests
npm test

# Run in watch mode
npm run test:watch

# Run with coverage
npm run test:coverage

# Run specific test file
npm test Header.test

# Type checking
npm run type-check
```

### Frontend Test Examples

#### Component Test Example

```typescript
describe("Login Component", () => {
  it("renders login form", () => {
    render(<Login />);

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /login/i })).toBeInTheDocument();
  });

  it("handles form submission", async () => {
    const mockLogin = jest.fn();
    render(<Login onLogin={mockLogin} />);

    await userEvent.type(screen.getByLabelText(/email/i), "test@example.com");
    await userEvent.type(screen.getByLabelText(/password/i), "password123");
    await userEvent.click(screen.getByRole("button", { name: /login/i }));

    expect(mockLogin).toHaveBeenCalledWith("test@example.com", "password123");
  });
});
```

#### API Integration Test Example

```typescript
it("fetches user bookings", async () => {
  // Mock API response
  global.fetch = jest.fn().mockResolvedValueOnce({
    ok: true,
    json: async () => [
      { id: "1", name: "Booking 1", start_time: "2024-01-01T10:00:00" },
    ],
  });

  render(<Dashboard />);

  await waitFor(() => {
    expect(screen.getByText("Booking 1")).toBeInTheDocument();
  });
});
```

### Type Checking (Frontend)

```bash
# Run TypeScript type checking
cd frontend
npm run type-check

# Type checking is included in test runner
python scripts/run_tests.py --frontend-only
```

## End-to-End Testing

### Scraper E2E Tests

The E2E tests verify the scraper works with the real Gibney website.

#### Setup

1. **Add Gibney credentials to `backend/.env`**:

   ```bash
   GIBNEY_EMAIL=your-email@example.com
   GIBNEY_PASSWORD=your-password
   ```

2. **Run E2E tests**:

   ```bash
   # Using test runner
   python scripts/run_tests.py --e2e

   # Or directly
   python backend/tests/test_scraper_e2e.py
   ```

#### What E2E Tests Cover

- Login functionality with real credentials
- Navigation to bookings page
- Infinite scroll handling
- Booking data extraction
- Error recovery mechanisms

### Manual Scraper Testing

```bash
# Test scraper independently
python scripts/test_scraper.py
```

This will:

1. Use credentials from `backend/.env`
2. Run scraper with visible browser (not headless)
3. Display found bookings
4. Save debug files on failure

## Test Coverage

### Viewing Coverage Reports

After running tests with `--coverage`:

- **Backend**: Open `htmlcov/index.html` in a browser
- **Frontend**: Open `frontend/coverage/lcov-report/index.html`

### Coverage Requirements

- Maintain minimum 80% test coverage
- New features must include tests
- Bug fixes should include regression tests

## Testing Best Practices

### General Guidelines

1. **Test Naming**: Use descriptive names that explain what is being tested
2. **Test Independence**: Each test should be able to run independently
3. **Test Data**: Use factories or fixtures for consistent test data
4. **Mocking**: Mock external dependencies (API calls, database, etc.)

### Backend Testing

1. **Use Fixtures**: Share common test setup using pytest fixtures
2. **Test Categories**: Mark tests as `unit` or `integration`
3. **Database Isolation**: Each test gets a fresh database
4. **API Testing**: Test both success and error cases

### Frontend Testing

1. **Component Testing**: Test components in isolation
2. **User Interaction**: Test from the user's perspective
3. **Async Handling**: Use `waitFor` for async operations
4. **Accessibility**: Include accessibility assertions

## Continuous Integration

Tests run automatically on:

- Every push to any branch
- Pull request creation/update
- Scheduled daily runs

GitHub Actions workflow:

1. Sets up Python and Node.js
2. Installs dependencies
3. Runs type checking
4. Runs backend tests with coverage
5. Runs frontend tests with coverage
6. Fails if any test fails or coverage drops

## Debugging Test Failures

### Backend Test Debugging

```bash
# Run with verbose output
pytest -v -s backend/tests/

# Run specific test with debugging
pytest -v -s -k "test_user_registration"

# Use Python debugger
import pdb; pdb.set_trace()
```

### Frontend Test Debugging

```bash
# Run single test file in watch mode
npm test -- --watch Header.test

# Debug in VS Code
# Add breakpoint and use "Debug CRA Tests" configuration
```

### Common Issues

1. **Database Locked**: Ensure no other processes are using test database
2. **Import Errors**: Check virtual environment is activated
3. **Async Warnings**: Use proper async test utilities
4. **Flaky Tests**: Check for timing issues or external dependencies

## Writing New Tests

### Backend Test Template

```python
import pytest
from backend.models import User

@pytest.mark.unit
class TestNewFeature:
    """Test suite for new feature"""

    def test_feature_behavior(self):
        """Test that feature behaves correctly"""
        # Arrange
        input_data = {"key": "value"}

        # Act
        result = new_feature_function(input_data)

        # Assert
        assert result == expected_value

    @pytest.mark.integration
    def test_feature_with_database(self, test_db):
        """Test feature with database interaction"""
        # Test implementation
```

### Frontend Test Template

```typescript
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NewComponent } from "../components/NewComponent";

describe("NewComponent", () => {
  it("renders correctly", () => {
    render(<NewComponent title="Test" />);
    expect(screen.getByText("Test")).toBeInTheDocument();
  });

  it("handles user interaction", async () => {
    const handleClick = jest.fn();
    render(<NewComponent onClick={handleClick} />);

    await userEvent.click(screen.getByRole("button"));
    expect(handleClick).toHaveBeenCalled();
  });
});
```

## Test Maintenance

### Regular Tasks

1. **Update Dependencies**: Keep testing libraries up to date
2. **Review Coverage**: Monitor coverage trends
3. **Fix Flaky Tests**: Address intermittent failures promptly
4. **Refactor Tests**: Keep tests clean and maintainable

### Test Review Checklist

- [ ] Tests pass locally
- [ ] New code has tests
- [ ] Tests are readable and well-named
- [ ] No hardcoded values or credentials
- [ ] Proper cleanup after tests
- [ ] Coverage maintained or improved
