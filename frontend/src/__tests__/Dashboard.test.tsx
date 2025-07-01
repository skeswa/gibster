import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Dashboard from '@/components/Dashboard';
import { apiClient } from '@/lib/api';

// Mock the API client
jest.mock('@/lib/api', () => ({
  apiClient: {
    get: jest.fn(),
    post: jest.fn(),
  },
}));

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
  }),
}));

// Mock window.location.reload
const mockReload = jest.fn();
Object.defineProperty(window, 'location', {
  value: {
    reload: mockReload,
    href: 'http://localhost:3000/dashboard',
  },
  writable: true,
});

const mockUser = {
  id: '1',
  email: 'test@example.com',
};

const mockBookings = [
  {
    id: '1',
    name: 'Dance Class',
    start_time: '2024-01-01T10:00:00Z',
    end_time: '2024-01-01T11:00:00Z',
    studio: 'Studio A',
    location: 'Downtown',
    status: 'confirmed',
    price: 25,
    record_url: 'https://example.com/booking/1',
    last_seen: '2024-01-01T09:00:00Z',
  },
];

const mockCalendarUrl = 'https://example.com/calendar/user1.ics';

describe('Dashboard - Session Expiry', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockReload.mockClear();
  });

  it('should handle 401 error when fetching sync status', async () => {
    // Mock the sync status call to return 401
    (apiClient.get as jest.Mock).mockRejectedValueOnce(
      new Error('Authentication required')
    );

    render(
      <Dashboard
        user={mockUser}
        bookings={mockBookings}
        calendarUrl={mockCalendarUrl}
      />
    );

    // Wait for the initial sync status fetch
    await waitFor(() => {
      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/user/sync/status');
    });

    // The component should still render without crashing
    expect(screen.getByText('Your Calendar Feed')).toBeInTheDocument();
  });

  it('should handle 401 error when starting manual sync', async () => {
    // Mock successful initial sync status
    (apiClient.get as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        job: {
          id: '1',
          status: 'completed',
          bookings_synced: 5,
          started_at: '2024-01-01T09:00:00Z',
          completed_at: '2024-01-01T09:05:00Z',
          triggered_manually: false,
        },
        last_sync_at: '2024-01-01T09:00:00Z',
      }),
    });

    // Mock the sync post to throw 401 error
    (apiClient.post as jest.Mock).mockRejectedValueOnce(
      new Error('Authentication required')
    );

    render(
      <Dashboard
        user={mockUser}
        bookings={mockBookings}
        calendarUrl={mockCalendarUrl}
      />
    );

    // Click the sync button
    const syncButton = await screen.findByRole('button', { name: /sync now/i });
    await userEvent.click(syncButton);

    // Wait for the error to be handled
    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith('/api/v1/user/sync');
    });

    // Component should still be functional
    expect(screen.getByText('Your Calendar Feed')).toBeInTheDocument();
  });

  it('should handle 401 during sync status polling', async () => {
    // Mock successful initial sync status
    (apiClient.get as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        job: {
          id: '1',
          status: 'completed',
          bookings_synced: 5,
          started_at: '2024-01-01T09:00:00Z',
          completed_at: '2024-01-01T09:05:00Z',
          triggered_manually: false,
        },
        last_sync_at: '2024-01-01T09:00:00Z',
      }),
    });

    // Mock successful sync start
    (apiClient.post as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        job_id: '2',
        message: 'Sync started',
      }),
    });

    // Mock sync history call that happens after sync start
    (apiClient.get as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        jobs: [
          {
            id: '1',
            status: 'completed',
            bookings_synced: 5,
            started_at: '2024-01-01T09:00:00Z',
            completed_at: '2024-01-01T09:05:00Z',
            triggered_manually: false,
          },
        ],
      }),
    });

    // Mock first status check successful, then 401
    (apiClient.get as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          job: {
            id: '2',
            status: 'running',
            progress: 'Fetching bookings...',
            bookings_synced: 0,
            started_at: '2024-01-01T10:00:00Z',
            triggered_manually: true,
          },
        }),
      })
      .mockRejectedValueOnce(new Error('Authentication required'));

    render(
      <Dashboard
        user={mockUser}
        bookings={mockBookings}
        calendarUrl={mockCalendarUrl}
      />
    );

    // Click the sync button
    const syncButton = await screen.findByRole('button', { name: /sync now/i });
    await userEvent.click(syncButton);

    // Wait for polling to occur
    await waitFor(
      () => {
        // Should have called get at least 4 times (initial, sync history, status after sync, polling)
        expect(apiClient.get).toHaveBeenCalledTimes(4);
      },
      { timeout: 3000 }
    );

    // Component should handle the error gracefully
    expect(screen.getByText('Your Calendar Feed')).toBeInTheDocument();
  });

  it('should display bookings correctly even if sync status fails', async () => {
    // Mock the sync status call to fail
    (apiClient.get as jest.Mock).mockRejectedValueOnce(
      new Error('Authentication required')
    );

    render(
      <Dashboard
        user={mockUser}
        bookings={mockBookings}
        calendarUrl={mockCalendarUrl}
      />
    );

    // Bookings should still be displayed
    expect(screen.getByText('Dance Class')).toBeInTheDocument();
    expect(screen.getByText('Studio A')).toBeInTheDocument();
    expect(screen.getByText('Downtown')).toBeInTheDocument();
  });

  it('should show calendar URL even if sync status fails', async () => {
    // Mock the sync status call to fail
    (apiClient.get as jest.Mock).mockRejectedValueOnce(
      new Error('Authentication required')
    );

    render(
      <Dashboard
        user={mockUser}
        bookings={mockBookings}
        calendarUrl={mockCalendarUrl}
      />
    );

    // Calendar URL should still be displayed
    expect(screen.getByText(/Or copy the URL manually:/i)).toBeInTheDocument();
    expect(screen.getByText(mockCalendarUrl)).toBeInTheDocument();
  });
});
