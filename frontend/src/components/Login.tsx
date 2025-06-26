import React, { useState } from 'react';
import Link from 'next/link';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || '';

interface User {
  id: string;
  email: string;
}

interface LoginProps {
  onLogin: (token: string, userData: User) => void;
}

interface FormData {
  email: string;
  password: string;
}

interface TokenResponse {
  access_token: string;
}

const Login: React.FC<LoginProps> = ({ onLogin }) => {
  const [formData, setFormData] = useState<FormData>({
    email: '',
    password: '',
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

    try {
      // Login request
      const loginFormData = new FormData();
      loginFormData.append('username', formData.email);
      loginFormData.append('password', formData.password);

      const response = await fetch(`${API_BASE}/api/v1/auth/token`, {
        method: 'POST',
        body: loginFormData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Login failed');
      }

      const tokenData: TokenResponse = await response.json();

      // Get user profile
      const profileResponse = await fetch(`${API_BASE}/api/v1/user/profile`, {
        headers: {
          Authorization: `Bearer ${tokenData.access_token}`,
        },
      });

      if (!profileResponse.ok) {
        throw new Error('Failed to get user profile');
      }

      const userData: User = await profileResponse.json();
      onLogin(tokenData.access_token, userData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className='card' style={{ maxWidth: '400px', margin: '2rem auto' }}>
      <h2 className='card-header'>Login to Gibster</h2>

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
              placeholder='Your password'
            />
          </div>

          <button
            type='submit'
            className='btn btn-primary'
            disabled={loading}
            style={{ width: '100%' }}
          >
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        <div className='text-center mt-2'>
          <p>
            Don't have an account? <Link href='/register'>Register here</Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
