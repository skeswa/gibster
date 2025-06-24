import React, { useState } from 'react';
import Link from 'next/link';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || '';

interface User {
  id: string;
  email: string;
  [key: string]: any;
}

interface RegisterProps {
  onLogin: (token: string, userData: User) => void;
}

interface FormData {
  email: string;
  password: string;
  confirmPassword: string;
}

interface TokenResponse {
  access_token: string;
}

const Register: React.FC<RegisterProps> = ({ onLogin }) => {
  const [formData, setFormData] = useState<FormData>({
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

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
    setError('');

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }

    try {
      // Register request
      const response = await fetch(`${API_BASE}/api/v1/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: formData.email,
          password: formData.password,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Registration failed');
      }

      const userData: User = await response.json();

      // Auto-login after registration
      const loginResponse = await fetch(`${API_BASE}/api/v1/auth/token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: formData.email,
          password: formData.password,
        }),
      });

      if (!loginResponse.ok) {
        throw new Error('Registration successful, but auto-login failed');
      }

      const tokenData: TokenResponse = await loginResponse.json();
      onLogin(tokenData.access_token, userData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className='card' style={{ maxWidth: '400px', margin: '2rem auto' }}>
      <h2 className='card-header'>Register for Gibster</h2>

      <div className='card-content'>
        {error && <div className='alert alert-error'>{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className='form-group'>
            <label htmlFor='email'>Email</label>
            <input
              type='email'
              id='email'
              name='email'
              value={formData.email}
              onChange={handleChange}
              required
              placeholder='your.email@example.com'
            />
          </div>

          <div className='form-group'>
            <label htmlFor='password'>Password</label>
            <input
              type='password'
              id='password'
              name='password'
              value={formData.password}
              onChange={handleChange}
              required
              placeholder='Choose a secure password'
              minLength={6}
            />
          </div>

          <div className='form-group'>
            <label htmlFor='confirmPassword'>Confirm Password</label>
            <input
              type='password'
              id='confirmPassword'
              name='confirmPassword'
              value={formData.confirmPassword}
              onChange={handleChange}
              required
              placeholder='Confirm your password'
              minLength={6}
            />
          </div>

          <button
            type='submit'
            className='btn btn-primary'
            disabled={loading}
            style={{ width: '100%' }}
          >
            {loading ? 'Creating Account...' : 'Register'}
          </button>
        </form>

        <div className='text-center mt-2'>
          <p>
            Already have an account? <Link href='/login'>Login here</Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Register;
