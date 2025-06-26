'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';

// Client-side API base URL
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

interface User {
  id: string;
  email: string;
  [key: string]: any;
}

interface Booking {
  id: string;
  name: string;
  start_time: string;
  end_time: string;
  studio: string;
  location: string;
  status: string;
  price?: number;
  record_url: string;
  last_seen: string;
}

interface SyncJob {
  id: string;
  status: string;
  progress?: string;
  bookings_synced: number;
  error_message?: string;
  started_at: string;
  completed_at?: string;
  triggered_manually: boolean;
}

interface SyncStatus {
  job: SyncJob;
  last_sync_at?: string;
}

interface DashboardProps {
  user: User;
  bookings: Booking[];
  calendarUrl: string;
}

const Dashboard: React.FC<DashboardProps> = ({
  user,
  bookings,
  calendarUrl,
}) => {
  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [syncMessage, setSyncMessage] = useState<string>('');
  const [isPolling, setIsPolling] = useState(false);

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone, // Use user's local timezone
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  };

  const formatCompactDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const formatTime = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  };

  const getStatusClass = (status: string): string => {
    const statusLower = status.toLowerCase();
    if (statusLower.includes('confirmed') || statusLower.includes('completed'))
      return 'status-confirmed';
    if (statusLower.includes('pending')) return 'status-pending';
    if (statusLower.includes('canceled')) return 'status-canceled';
    return 'status-confirmed';
  };

  const getSyncStatusClass = (status: string): string => {
    switch (status) {
      case 'completed':
        return 'status-success';
      case 'failed':
        return 'status-error';
      case 'running':
        return 'status-running';
      case 'pending':
        return 'status-pending';
      default:
        return 'status-neutral';
    }
  };

  // Fetch sync status
  const fetchSyncStatus = async () => {
    try {
      const token = document.cookie
        .split('; ')
        .find(row => row.startsWith('token='))
        ?.split('=')[1];

      if (!token) return;

      const response = await fetch(`${API_BASE}/api/v1/user/sync/status`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        const status = await response.json();
        setSyncStatus(status);
      }
    } catch (error) {
      console.error('Failed to fetch sync status:', error);
    }
  };

  // Start manual sync
  const handleSyncNow = async () => {
    setIsLoading(true);
    setSyncMessage('');

    try {
      const token = document.cookie
        .split('; ')
        .find(row => row.startsWith('token='))
        ?.split('=')[1];

      if (!token) {
        setSyncMessage('Authentication required');
        setIsLoading(false);
        return;
      }

      const response = await fetch(`${API_BASE}/api/v1/user/sync`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        const result = await response.json();
        setSyncMessage(
          'Sync started successfully! Checking for updates...'
        );
        setIsPolling(true);

        // Immediately fetch the initial status
        await fetchSyncStatus();

        // Start polling for status updates after a short delay
        setTimeout(() => {
          const interval = setInterval(async () => {
            try {
              const token = document.cookie
                .split('; ')
                .find(row => row.startsWith('token='))
                ?.split('=')[1];

              if (!token) {
                clearInterval(interval);
                setIsLoading(false);
                setIsPolling(false);
                return;
              }

              const statusResponse = await fetch(`${API_BASE}/api/v1/user/sync/status`, {
                headers: { Authorization: `Bearer ${token}` },
              });

              if (statusResponse.ok) {
                const freshStatus = await statusResponse.json();
                setSyncStatus(freshStatus);

                // Update message based on current status
                if (freshStatus?.job?.status === 'running') {
                  setSyncMessage(
                    `Sync in progress... ${freshStatus.job.progress || 'Fetching your bookings from Gibney'}`
                  );
                }

                // Check the fresh status, not the stale component state
                if (freshStatus?.job?.status === 'completed' || freshStatus?.job?.status === 'failed') {
                  clearInterval(interval);
                  setIsLoading(false);
                  setIsPolling(false);

                  if (freshStatus.job.status === 'completed') {
                    setSyncMessage(
                      `Sync completed! ${freshStatus.job.bookings_synced} bookings were synced.`
                    );
                    // Refresh the page to show updated bookings
                    setTimeout(() => window.location.reload(), 2000);
                  } else {
                    setSyncMessage(
                      `Sync failed: ${freshStatus.job.error_message || 'Unknown error'}`
                    );
                  }
                }
              } else {
                console.error('Failed to fetch sync status during polling');
              }
            } catch (error) {
              console.error('Error during status polling:', error);
            }
          }, 1500); // Poll every 1.5 seconds for more responsive updates

          // Stop polling after 5 minutes to avoid infinite polling
          setTimeout(() => {
            clearInterval(interval);
            setIsLoading(false);
            setIsPolling(false);
            setSyncMessage('Sync is taking longer than expected. Please check back later or try again.');
          }, 300000);
        }, 500); // Wait 500ms before starting polling to allow job creation

      } else {
        const error = await response.json();
        setSyncMessage(
          `Failed to start sync: ${error.detail || 'Unknown error'}`
        );
        setIsLoading(false);
      }
    } catch (error) {
      setSyncMessage('Failed to start sync. Please try again.');
      setIsLoading(false);
    }
  };

  // Fetch initial sync status
  useEffect(() => {
    fetchSyncStatus();
  }, []);

  return (
    <div className='dashboard-container'>
      <div className='grid grid-2'>
        {/* Calendar URL Card */}
        <div className='card'>
          <h2 className='card-header'>Your Calendar Feed</h2>
          <div className='card-content'>
            {calendarUrl ? (
              <>
                <p className='mb-1'>
                  Add this URL to your calendar app to sync your Gibney
                  bookings:
                </p>
                <div
                  style={{
                    background: '#f8f9fa',
                    padding: '1rem',
                    borderRadius: '8px',
                    wordBreak: 'break-all',
                    marginBottom: '1rem',
                    fontFamily: 'monospace',
                    fontSize: '0.9rem',
                  }}
                >
                  <code>{calendarUrl}</code>
                </div>
                <p className='mb-1'>
                  <em>
                    Select and copy the URL above to add to your calendar app.
                  </em>
                </p>
              </>
            ) : (
              <p>Loading calendar URL...</p>
            )}
          </div>
        </div>

        {/* Sync Control Card */}
        <div className='card'>
          <h2 className='card-header'>Sync Settings</h2>
          <div className='card-content'>
            <p className='mb-1'>
              Sync your latest Gibney bookings. Your calendar will automatically
              update every 2 hours, or you can manually sync now.
            </p>

            {syncStatus && syncStatus.last_sync_at && (
              <p className='mb-1 text-muted'>
                Last sync: {formatDate(syncStatus.last_sync_at)}
              </p>
            )}

            <div className='mb-1'>
              <button
                onClick={handleSyncNow}
                disabled={isLoading || isPolling}
                className={`btn ${isLoading || isPolling ? 'btn-disabled' : 'btn-primary'}`}
                style={{ marginRight: '1rem' }}
              >
                {isLoading 
                  ? 'Starting Sync...' 
                  : isPolling 
                    ? 'Syncing...' 
                    : 'Sync Now'}
              </button>

              <Link href='/credentials' className='btn btn-outline'>
                Update Gibney Credentials
              </Link>
            </div>

            {/* Sync Status Display */}
            {syncStatus && (
              <div
                className='sync-status'
                style={{
                  marginTop: '1rem',
                  padding: '1rem',
                  background: '#f8f9fa',
                  borderRadius: '8px',
                }}
              >
                <h4>Sync Status</h4>
                <div
                  className={`badge ${getSyncStatusClass(syncStatus.job.status)}`}
                >
                  {syncStatus.job.status.replace('_', ' ').toUpperCase()}
                </div>
                {syncStatus.job.progress && (
                  <p style={{ margin: '0.5rem 0', fontSize: '0.9rem' }}>
                    {syncStatus.job.progress}
                  </p>
                )}
                {syncStatus.job.bookings_synced > 0 && (
                  <p style={{ margin: '0.5rem 0', fontSize: '0.9rem' }}>
                    Bookings synced: {syncStatus.job.bookings_synced}
                  </p>
                )}
                {syncStatus.job.error_message && (
                  <p
                    style={{
                      margin: '0.5rem 0',
                      fontSize: '0.9rem',
                      color: '#dc3545',
                    }}
                  >
                    Error: {syncStatus.job.error_message}
                  </p>
                )}
              </div>
            )}

            {syncMessage && (
              <div
                className='sync-message'
                style={{
                  marginTop: '1rem',
                  padding: '1rem',
                  background: isPolling ? '#fff3cd' : '#e3f2fd',
                  borderRadius: '8px',
                  border: isPolling ? '1px solid #ffeaa7' : '1px solid #b3d4fc',
                }}
              >
                {isPolling && (
                  <span style={{ marginRight: '0.5rem' }}>
                    ⏳
                  </span>
                )}
                {syncMessage}
              </div>
            )}

            <p
              className='mb-1'
              style={{ marginTop: '1rem', fontSize: '0.9rem', color: '#666' }}
            >
              <em>
                Manual sync may take a few moments to complete. The page will
                refresh automatically when finished.
              </em>
            </p>
          </div>
        </div>
      </div>

      {/* Bookings Table */}
      <div className='card bookings-card'>
        <h2 className='card-header'>Your Bookings ({bookings.length})</h2>
        <div className='card-content'>
          {bookings.length === 0 ? (
            <div className='text-center py-2'>
              <p>No bookings found.</p>
              <p>
                Sync your Gibney account to see your bookings here, or{' '}
                <Link href='/credentials'>update your credentials</Link> if you
                haven't set them yet.
              </p>
            </div>
          ) : (
            <div className='bookings-table-container'>
              <table className='bookings-table'>
                <thead>
                  <tr>
                    <th className='booking-name-col'>Booking</th>
                    <th className='date-col'>Date</th>
                    <th className='time-col'>Time</th>
                    <th className='studio-col'>Studio</th>
                    <th className='status-col'>Status</th>
                    <th className='price-col'>Price</th>
                    <th className='actions-col'>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {bookings.map(booking => (
                    <tr key={booking.id}>
                      <td className='booking-name-cell'>
                        <div className='booking-name'>{booking.name}</div>
                      </td>
                      <td className='date-cell'>
                        <div className='booking-date'>
                          {formatCompactDate(booking.start_time)}
                        </div>
                      </td>
                      <td className='time-cell'>
                        <div className='booking-time'>
                          <div>{formatTime(booking.start_time)}</div>
                          <div className='time-separator'>to</div>
                          <div>{formatTime(booking.end_time)}</div>
                        </div>
                      </td>
                      <td className='studio-cell'>
                        <div className='studio-info'>
                          <div className='studio-name'>{booking.studio}</div>
                          <div className='studio-location'>
                            {booking.location}
                          </div>
                        </div>
                      </td>
                      <td className='status-cell'>
                        <span
                          className={`status-badge ${getStatusClass(booking.status)}`}
                        >
                          {booking.status}
                        </span>
                      </td>
                      <td className='price-cell'>
                        <div className='booking-price'>
                          {booking.price ? `$${booking.price}` : 'Free'}
                        </div>
                      </td>
                      <td className='actions-cell'>
                        <a
                          href={booking.record_url}
                          target='_blank'
                          rel='noopener noreferrer'
                          className='btn btn-sm btn-secondary action-btn'
                        >
                          View Details
                        </a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
