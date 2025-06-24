import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

const API_BASE = process.env.REACT_APP_API_BASE || '';

const Dashboard = ({ user }) => {
  const [bookings, setBookings] = useState([]);
  const [calendarUrl, setCalendarUrl] = useState('');
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    const token = localStorage.getItem('token');

    try {
      // Load bookings and calendar URL in parallel
      const [bookingsResponse, calendarResponse] = await Promise.all([
        fetch(`${API_BASE}/api/v1/user/bookings`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${API_BASE}/api/v1/user/calendar_url`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ]);

      if (bookingsResponse.ok) {
        const bookingsData = await bookingsResponse.json();
        setBookings(bookingsData);
      }

      if (calendarResponse.ok) {
        const calendarData = await calendarResponse.json();
        setCalendarUrl(calendarData.calendar_url);
      }
    } catch (err) {
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    setMessage('');
    setError('');
    
    const token = localStorage.getItem('token');

    try {
      const response = await fetch(`${API_BASE}/api/v1/user/sync`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Sync failed');
      }

      const result = await response.json();
      setMessage(result.message);
      
      // Reload bookings after sync
      loadDashboardData();
    } catch (err) {
      setError(err.message);
    } finally {
      setSyncing(false);
    }
  };

  const copyCalendarUrl = () => {
    navigator.clipboard.writeText(calendarUrl).then(() => {
      setMessage('Calendar URL copied to clipboard!');
      setTimeout(() => setMessage(''), 3000);
    });
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const getStatusClass = (status) => {
    const statusLower = status.toLowerCase();
    if (statusLower.includes('confirmed')) return 'status-confirmed';
    if (statusLower.includes('pending')) return 'status-pending';
    if (statusLower.includes('canceled')) return 'status-canceled';
    return 'status-confirmed';
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <p>Loading dashboard...</p>
      </div>
    );
  }

  return (
    <div className="grid grid-2">
      {/* Calendar URL Card */}
      <div className="card">
        <h2 className="card-header">Your Calendar Feed</h2>
        <div className="card-content">
          {calendarUrl ? (
            <>
              <p className="mb-1">
                Add this URL to your calendar app to sync your Gibney bookings:
              </p>
              <div style={{ 
                background: '#f8f9fa', 
                padding: '1rem', 
                borderRadius: '8px', 
                wordBreak: 'break-all',
                marginBottom: '1rem'
              }}>
                <code>{calendarUrl}</code>
              </div>
              <button onClick={copyCalendarUrl} className="btn btn-primary">
                Copy URL
              </button>
              <div className="mt-2">
                <p><strong>Instructions:</strong></p>
                <ul style={{ paddingLeft: '1.5rem', lineHeight: '1.6' }}>
                  <li><strong>Google Calendar:</strong> Settings → Add calendar → From URL</li>
                  <li><strong>Apple Calendar:</strong> File → New Calendar Subscription</li>
                  <li><strong>Outlook:</strong> Calendar → Add calendar → Subscribe from web</li>
                </ul>
              </div>
            </>
          ) : (
            <p>Loading calendar URL...</p>
          )}
        </div>
      </div>

      {/* Sync Control Card */}
      <div className="card">
        <h2 className="card-header">Sync Settings</h2>
        <div className="card-content">
          {message && (
            <div className="alert alert-success">
              {message}
            </div>
          )}
          
          {error && (
            <div className="alert alert-error">
              {error}
            </div>
          )}

          <p className="mb-1">
            Sync your latest Gibney bookings. Your calendar will automatically 
            update every 2 hours, or you can manually sync now.
          </p>
          
          <button 
            onClick={handleSync} 
            className="btn btn-primary"
            disabled={syncing}
          >
            {syncing ? 'Syncing...' : 'Sync Now'}
          </button>
          
          <Link to="/credentials" className="btn btn-secondary ml-1">
            Update Gibney Credentials
          </Link>
        </div>
      </div>

      {/* Bookings Table */}
      <div className="card" style={{ gridColumn: '1 / -1' }}>
        <h2 className="card-header">Your Bookings ({bookings.length})</h2>
        <div className="card-content">
          {bookings.length === 0 ? (
            <div className="text-center">
              <p>No bookings found.</p>
              <p>
                <Link to="/credentials">Add your Gibney credentials</Link> and 
                sync to see your bookings here.
              </p>
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table className="table">
                <thead>
                  <tr>
                    <th>Rental</th>
                    <th>Start Time</th>
                    <th>End Time</th>
                    <th>Studio</th>
                    <th>Location</th>
                    <th>Status</th>
                    <th>Price</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {bookings.map((booking) => (
                    <tr key={booking.id}>
                      <td><strong>{booking.name}</strong></td>
                      <td>{formatDate(booking.start_time)}</td>
                      <td>{formatDate(booking.end_time)}</td>
                      <td>{booking.studio}</td>
                      <td>{booking.location}</td>
                      <td>
                        <span className={`status-badge ${getStatusClass(booking.status)}`}>
                          {booking.status}
                        </span>
                      </td>
                      <td>{booking.price ? `$${booking.price}` : '-'}</td>
                      <td>
                        <a 
                          href={booking.record_url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="btn btn-secondary"
                          style={{ fontSize: '0.8rem', padding: '0.25rem 0.5rem' }}
                        >
                          View
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