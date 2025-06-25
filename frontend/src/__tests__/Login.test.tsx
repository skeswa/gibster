import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import Login from '@/components/Login';

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
  }),
}));

// Mock fetch
global.fetch = jest.fn();

describe('Login Component', () => {
  beforeEach(() => {
    (fetch as jest.MockedFunction<typeof fetch>).mockClear();
  });

  test('renders login form with email and password fields', () => {
    const mockOnLogin = jest.fn();
    render(<Login onLogin={mockOnLogin} />);

    expect(screen.getByText('Login to Gibster')).toBeInTheDocument();
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Login' })).toBeInTheDocument();
    expect(screen.getByText("Don't have an account?")).toBeInTheDocument();
  });

  test('updates form fields when user types', () => {
    const mockOnLogin = jest.fn();
    render(<Login onLogin={mockOnLogin} />);

    const emailInput = screen.getByLabelText('Email') as HTMLInputElement;
    const passwordInput = screen.getByLabelText('Password') as HTMLInputElement;

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });

    expect(emailInput.value).toBe('test@example.com');
    expect(passwordInput.value).toBe('password123');
  });

  test('shows loading state when form is submitted', async () => {
    const mockOnLogin = jest.fn();
    render(<Login onLogin={mockOnLogin} />);

    // Create a promise we can control
    let resolveTokenRequest!: (value: any) => void;
    let resolveProfileRequest!: (value: any) => void;
    
    const tokenPromise = new Promise((resolve) => {
      resolveTokenRequest = resolve;
    });
    
    const profilePromise = new Promise((resolve) => {
      resolveProfileRequest = resolve;
    });

    // Mock responses with controlled promises
    (fetch as jest.MockedFunction<typeof fetch>)
      .mockReturnValueOnce(tokenPromise as any)
      .mockReturnValueOnce(profilePromise as any);

    const emailInput = screen.getByLabelText('Email');
    const passwordInput = screen.getByLabelText('Password');
    const submitButton = screen.getByRole('button', { name: 'Login' });

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    
    // Click submit
    fireEvent.click(submitButton);

    // Check loading state appears immediately
    await waitFor(() => {
      expect(screen.getByText('Logging in...')).toBeInTheDocument();
      expect(submitButton).toBeDisabled();
    });

    // Now resolve the requests
    resolveTokenRequest({
      ok: true,
      json: () => Promise.resolve({ access_token: 'test-token' }),
    });

    resolveProfileRequest({
      ok: true,
      json: () => Promise.resolve({ id: '1', email: 'test@example.com' }),
    });

    // Wait for completion
    await waitFor(() => {
      expect(mockOnLogin).toHaveBeenCalledWith('test-token', {
        id: '1',
        email: 'test@example.com',
      });
    });
  });

  test('displays error message when login fails', async () => {
    const mockOnLogin = jest.fn();
    render(<Login onLogin={mockOnLogin} />);

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
    
    await act(async () => {
      fireEvent.click(submitButton);
    });

    await waitFor(() => {
      expect(screen.getByText('Invalid credentials')).toBeInTheDocument();
    });

    expect(mockOnLogin).not.toHaveBeenCalled();
  });
});
