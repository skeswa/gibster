import React from 'react';
import Link from 'next/link';
import LogoutButton from '@/components/LogoutButton';
import type { User } from '@/lib/auth';

interface ServerHeaderProps {
  user: User | null;
}

export default function ServerHeader({ user }: ServerHeaderProps) {
  return (
    <header className='header'>
      <h1>Gibster</h1>

      <nav>
        {user ? (
          <>
            <span className='user-info'>Welcome, {user.email}</span>
            <Link href='/dashboard' className='btn btn-secondary'>
              Dashboard
            </Link>
            <Link href='/credentials' className='btn btn-secondary'>
              Settings
            </Link>
            <LogoutButton />
          </>
        ) : (
          <>
            <Link href='/login' className='btn btn-primary'>
              Login
            </Link>
            <Link href='/register' className='btn btn-secondary'>
              Register
            </Link>
          </>
        )}
      </nav>
    </header>
  );
}
