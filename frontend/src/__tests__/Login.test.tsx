import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Login from '../components/Login';

const renderWithRouter = (ui: React.ReactElement) => {
  return render(<BrowserRouter>{ui}</BrowserRouter>);
};

// Mock fetch
global.fetch = jest.fn();

describe('Login Component', () => {
  beforeEach(() => {
    (fetch as jest.MockedFunction<typeof fetch>).mockClear();
  });

  test('renders login form with email and password fields', () => {
    const mockOnLogin = jest.fn();
    renderWithRouter(<Login onLogin={mockOnLogin} />);

    expect(screen.getByText('Login to Gibster')).toBeInTheDocument();
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Login' })).toBeInTheDocument();
    expect(screen.getByText("Don't have an account?")).toBeInTheDocument();
  });

  test('updates form fields when user types', () => {
    const mockOnLogin = jest.fn();
    renderWithRouter(<Login onLogin={mockOnLogin} />);

    const emailInput = screen.getByLabelText('Email') as HTMLInputElement;
    const passwordInput = screen.getByLabelText('Password') as HTMLInputElement;

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });

    expect(emailInput.value).toBe('test@example.com');
    expect(passwordInput.value).toBe('password123');
  });

  test('shows loading state when form is submitted', async () => {
    const mockOnLogin = jest.fn();
    renderWithRouter(<Login onLogin={mockOnLogin} />);

    // Mock successful login response
    (fetch as jest.MockedFunction<typeof fetch>)
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ access_token: 'test-token' }),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ id: '1', email: 'test@example.com' }),
      } as Response);

    const emailInput = screen.getByLabelText('Email');
    const passwordInput = screen.getByLabelText('Password');
    const submitButton = screen.getByRole('button', { name: 'Login' });

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.click(submitButton);

    expect(screen.getByText('Logging in...')).toBeInTheDocument();
    expect(submitButton).toBeDisabled();
  });

  test('displays error message when login fails', async () => {
    const mockOnLogin = jest.fn();
    renderWithRouter(<Login onLogin={mockOnLogin} />);

    // Mock failed login response
    (fetch as jest.MockedFunction<typeof fetch>).mockResolvedValueOnce({
      ok: false,
      json: () => Promise.resolve({ detail: 'Invalid credentials' }),
    } as Response);

    const emailInput = screen.getByLabelText('Email');
    const passwordInput = screen.getByLabelText('Password');
    const submitButton = screen.getByRole('button', { name: 'Login' });

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'wrongpassword' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Invalid credentials')).toBeInTheDocument();
    });

    expect(mockOnLogin).not.toHaveBeenCalled();
  });
});
