import React from 'react';
import Link from 'next/link';

import CredentialsForm from './CredentialsForm';

interface User {
  id: string;
  email: string;
  [key: string]: any;
}

interface CredentialsProps {
  user: User;
}

const Credentials: React.FC<CredentialsProps> = ({ user }) => {
  return (
    <div className='card' style={{ maxWidth: '600px', margin: '2rem auto' }}>
      <h2 className='card-header'>Gibney Credentials</h2>

      <div className='card-content'>
        <div className='alert alert-info'>
          <strong>Privacy Notice:</strong> Your Gibney credentials are encrypted
          and stored securely. They are only used to sync your bookings and are
          never shared with third parties.
        </div>

        {/* Client component for interactive form */}
        <CredentialsForm />

        <div style={{ marginTop: '1rem' }}>
          <Link href='/dashboard' className='btn btn-secondary'>
            Back to Dashboard
          </Link>
        </div>

        <div
          className='mt-2'
          style={{
            background: '#f8f9fa',
            padding: '1.5rem',
            borderRadius: '8px',
            marginTop: '2rem',
          }}
        >
          <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem' }}>
            How it works:
          </h3>
          <ol style={{ paddingLeft: '1.5rem', lineHeight: '1.6' }}>
            <li>Enter your Gibney credentials here</li>
            <li>Gibster will automatically sync your bookings every 2 hours</li>
            <li>Your calendar feed will be updated with the latest bookings</li>
            <li>
              Subscribe to your calendar feed in your favorite calendar app
            </li>
          </ol>

          <p style={{ marginTop: '1rem', marginBottom: '0' }}>
            <strong>Need help?</strong> Visit{' '}
            <a
              href='https://gibney.my.site.com/'
              target='_blank'
              rel='noopener noreferrer'
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
