import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Header from '@/components/Header';

const mockUser = {
  id: '1',
  email: 'test@example.com',
};

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
  }),
}));

describe('Header Component', () => {
  test('renders login and register links when user is not logged in', () => {
    const mockLogout = jest.fn();
    render(<Header user={null} onLogout={mockLogout} />);

    expect(screen.getByText('Gibster')).toBeInTheDocument();
    expect(screen.getByText('Login')).toBeInTheDocument();
    expect(screen.getByText('Sign Up')).toBeInTheDocument();
  });

  test('renders user info and navigation when user is logged in', () => {
    const mockLogout = jest.fn();
    render(<Header user={mockUser} onLogout={mockLogout} />);

    expect(screen.getByText('Gibster')).toBeInTheDocument();
    expect(screen.getByText(mockUser.email)).toBeInTheDocument();
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Settings')).toBeInTheDocument();
    expect(screen.getByText('Logout')).toBeInTheDocument();
  });

  test('calls onLogout when logout button is clicked', () => {
    const mockLogout = jest.fn();
    render(<Header user={mockUser} onLogout={mockLogout} />);

    const logoutButton = screen.getByText('Logout');
    fireEvent.click(logoutButton);

    expect(mockLogout).toHaveBeenCalledTimes(1);
  });
});
