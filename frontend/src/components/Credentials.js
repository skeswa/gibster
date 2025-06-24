import React, { useState } from 'react';
import { Link } from 'react-router-dom';

const API_BASE = process.env.REACT_APP_API_BASE || '';

const Credentials = ({ user }) => {
  const [formData, setFormData] = useState({
    gibney_email: '',
    gibney_password: ''
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');
    setError('');

    const token = localStorage.getItem('token');

    try {
      const response = await fetch(`${API_BASE}/api/v1/user/credentials`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update credentials');
      }

      const result = await response.json();
      setMessage(result.message);
      
      // Clear form
      setFormData({
        gibney_email: '',
        gibney_password: ''
      });

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card" style={{ maxWidth: '600px', margin: '2rem auto' }}>
      <h2 className="card-header">Gibney Credentials</h2>
      
      <div className="card-content">
        <div className="alert alert-info">
          <strong>Privacy Notice:</strong> Your Gibney credentials are encrypted and stored securely. 
          They are only used to sync your bookings and are never shared with third parties.
        </div>

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

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="gibney_email">Gibney Email</label>
            <input
              type="email"
              id="gibney_email"
              name="gibney_email"
              value={formData.gibney_email}
              onChange={handleChange}
              required
              placeholder="Your Gibney account email"
            />
            <small style={{ color: '#666', fontSize: '0.9rem' }}>
              The email you use to log into gibney.my.site.com
            </small>
          </div>

          <div className="form-group">
            <label htmlFor="gibney_password">Gibney Password</label>
            <input
              type="password"
              id="gibney_password"
              name="gibney_password"
              value={formData.gibney_password}
              onChange={handleChange}
              required
              placeholder="Your Gibney account password"
            />
            <small style={{ color: '#666', fontSize: '0.9rem' }}>
              Your password will be encrypted before storage
            </small>
          </div>

          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
            <button 
              type="submit" 
              className="btn btn-primary" 
              disabled={loading}
            >
              {loading ? 'Updating...' : 'Update Credentials'}
            </button>
            
            <Link to="/dashboard" className="btn btn-secondary">
              Back to Dashboard
            </Link>
          </div>
        </form>

        <div className="mt-2" style={{ 
          background: '#f8f9fa', 
          padding: '1.5rem', 
          borderRadius: '8px',
          marginTop: '2rem'
        }}>
          <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem' }}>How it works:</h3>
          <ol style={{ paddingLeft: '1.5rem', lineHeight: '1.6' }}>
            <li>Enter your Gibney credentials here</li>
            <li>Gibster will automatically sync your bookings every 2 hours</li>
            <li>Your calendar feed will be updated with the latest bookings</li>
            <li>Subscribe to your calendar feed in your favorite calendar app</li>
          </ol>
          
          <p style={{ marginTop: '1rem', marginBottom: '0' }}>
            <strong>Need help?</strong> Visit{' '}
            <a 
              href="https://gibney.my.site.com/" 
              target="_blank" 
              rel="noopener noreferrer"
            >
              gibney.my.site.com
            </a>{' '}
            to check your login credentials or reset your password.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Credentials; 