import React from 'react';
import Link from 'next/link';

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

interface DashboardProps {
  user: User;
  bookings: Booking[];
  calendarUrl: string;
}

const Dashboard: React.FC<DashboardProps> = ({ user, bookings, calendarUrl }) => {
  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleString();
  };

  const getStatusClass = (status: string): string => {
    const statusLower = status.toLowerCase();
    if (statusLower.includes('confirmed')) return 'status-confirmed';
    if (statusLower.includes('pending')) return 'status-pending';
    if (statusLower.includes('canceled')) return 'status-canceled';
    return 'status-confirmed';
  };

  return (
    <div className='grid grid-2'>
      {/* Calendar URL Card */}
      <div className='card'>
        <h2 className='card-header'>Your Calendar Feed</h2>
        <div className='card-content'>
          {calendarUrl ? (
            <>
              <p className='mb-1'>
                Add this URL to your calendar app to sync your Gibney bookings:
              </p>
              <div
                style={{
                  background: '#f8f9fa',
                  padding: '1rem',
                  borderRadius: '8px',
                  wordBreak: 'break-all',
                  marginBottom: '1rem',
                }}
              >
                <code>{calendarUrl}</code>
              </div>
              <p className='mb-1'>
                <em>Select and copy the URL above to add to your calendar app.</em>
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

          <p className='mb-1'>
            <em>Note: Manual sync requires a page refresh to see updated data.</em>
          </p>

          <Link href='/credentials' className='btn btn-secondary'>
            Update Gibney Credentials
          </Link>
        </div>
      </div>

      {/* Bookings Table */}
      <div className='card grid-full'>
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
            <div className='table-responsive'>
              <table className='table'>
                <thead>
                  <tr>
                    <th>Booking</th>
                    <th>Date & Time</th>
                    <th>Studio</th>
                    <th>Status</th>
                    <th>Price</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {bookings.map((booking) => (
                    <tr key={booking.id}>
                      <td>
                        <strong>{booking.name}</strong>
                      </td>
                      <td>
                        <div>
                          <div>{formatDate(booking.start_time)}</div>
                          <div className='text-muted'>
                            to {formatDate(booking.end_time)}
                          </div>
                        </div>
                      </td>
                      <td>
                        <div>
                          <div>{booking.studio}</div>
                          <div className='text-muted'>{booking.location}</div>
                        </div>
                      </td>
                      <td>
                        <span className={`badge ${getStatusClass(booking.status)}`}>
                          {booking.status}
                        </span>
                      </td>
                      <td>
                        {booking.price ? `$${booking.price}` : 'Free'}
                      </td>
                      <td>
                        <a
                          href={booking.record_url}
                          target='_blank'
                          rel='noopener noreferrer'
                          className='btn btn-sm btn-secondary'
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
