'use client';

import React, { useState, useEffect } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || '';

interface FormData {
  gibney_email: string;
  gibney_password: string;
}

interface CredentialsResponse {
  message: string;
}

interface CredentialsEmailResponse {
  gibney_email: string | null;
}

const CredentialsForm: React.FC = () => {
  const [formData, setFormData] = useState<FormData>({
    gibney_email: '',
    gibney_password: '',
  });
  const [loading, setLoading] = useState<boolean>(false);
  const [message, setMessage] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [hasExistingCredentials, setHasExistingCredentials] =
    useState<boolean>(false);

  // Fetch existing email on component mount
  useEffect(() => {
    const fetchExistingEmail = async () => {
      const token = localStorage.getItem('token');
      if (!token) return;

      try {
        const response = await fetch(
          `${API_BASE}/api/v1/user/credentials/email`,
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        );

        if (response.ok) {
          const data: CredentialsEmailResponse = await response.json();
          if (data.gibney_email) {
            setFormData(prev => ({
              ...prev,
              gibney_email: data.gibney_email || '',
            }));
            setHasExistingCredentials(true);
          }
        }
      } catch (error) {
        // Silently handle error - user can still enter email manually
        console.error('Failed to fetch existing email:', error);
      }
    };

    fetchExistingEmail();
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (
    e: React.FormEvent<HTMLFormElement>
  ): Promise<void> => {
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
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update credentials');
      }

      const result: CredentialsResponse = await response.json();
      setMessage(`${result.message} - Password field cleared for security.`);

      // Only clear the password field for security, keep email
      setFormData(prev => ({
        ...prev,
        gibney_password: '',
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {message && <div className='alert alert-success'>{message}</div>}

      {error && <div className='alert alert-error'>{error}</div>}

      <form onSubmit={handleSubmit}>
        <div className='form-group'>
          <label htmlFor='gibney_email'>Gibney Email</label>
          <input
            type='email'
            id='gibney_email'
            name='gibney_email'
            value={formData.gibney_email}
            onChange={handleChange}
            required
            placeholder='Your Gibney account email'
          />
          <small style={{ color: '#666', fontSize: '0.9rem' }}>
            The email you use to log into gibney.my.site.com
          </small>
        </div>

        <div className='form-group'>
          <label htmlFor='gibney_password'>Gibney Password</label>
          <input
            type='password'
            id='gibney_password'
            name='gibney_password'
            value={formData.gibney_password}
            onChange={handleChange}
            required
            placeholder={
              hasExistingCredentials
                ? 'Enter new password or leave current password unchanged'
                : 'Your Gibney account password'
            }
          />
          <small style={{ color: '#666', fontSize: '0.9rem' }}>
            {hasExistingCredentials
              ? 'Password is saved. Enter a new one only if you want to change it.'
              : 'Your password will be encrypted before storage'}
          </small>
        </div>

        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
          <button type='submit' className='btn btn-primary' disabled={loading}>
            {loading ? 'Updating...' : 'Update Credentials'}
          </button>
        </div>
      </form>
    </>
  );
};

export default CredentialsForm;
