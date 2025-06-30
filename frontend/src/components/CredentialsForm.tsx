'use client';

import React, { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Loader2, Lock, CheckCircle2, AlertCircle } from 'lucide-react';

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
      try {
        const response = await apiClient.get('/api/v1/user/credentials/email');

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

    try {
      const response = await apiClient.put('/api/v1/user/credentials', formData);

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
    <Card className='w-full max-w-2xl'>
      <CardHeader>
        <CardTitle className='flex items-center gap-2'>
          <Lock className='h-5 w-5' />
          Gibney Credentials
        </CardTitle>
        <CardDescription>
          Connect your Gibney account to sync your bookings
        </CardDescription>
      </CardHeader>
      <CardContent>
        {message && (
          <Alert className='mb-6'>
            <CheckCircle2 className='h-4 w-4' />
            <AlertDescription>{message}</AlertDescription>
          </Alert>
        )}

        {error && (
          <Alert variant='destructive' className='mb-6'>
            <AlertCircle className='h-4 w-4' />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <form onSubmit={handleSubmit} className='space-y-6'>
          <div className='space-y-2'>
            <Label htmlFor='gibney_email'>Gibney Email</Label>
            <Input
              type='email'
              id='gibney_email'
              name='gibney_email'
              value={formData.gibney_email}
              onChange={handleChange}
              required
              placeholder='your@email.com'
              disabled={loading}
            />
            <p className='text-sm text-muted-foreground'>
              The email you use to log into gibney.my.site.com
            </p>
          </div>

          <div className='space-y-2'>
            <Label htmlFor='gibney_password'>Gibney Password</Label>
            <Input
              type='password'
              id='gibney_password'
              name='gibney_password'
              value={formData.gibney_password}
              onChange={handleChange}
              required
              placeholder={
                hasExistingCredentials
                  ? 'Enter new password to update'
                  : '••••••••'
              }
              disabled={loading}
            />
            <p className='text-sm text-muted-foreground'>
              {hasExistingCredentials
                ? 'Password is saved. Enter a new one only if you want to change it.'
                : 'Your password will be encrypted before storage'}
            </p>
          </div>

          <Button type='submit' disabled={loading}>
            {loading ? (
              <>
                <Loader2 className='mr-2 h-4 w-4 animate-spin' />
                Updating...
              </>
            ) : (
              'Update Credentials'
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
};

export default CredentialsForm;
