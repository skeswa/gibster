'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from './providers/AuthProvider';

export default function HomePage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading) {
      if (user) {
        router.push('/dashboard');
      } else {
        router.push('/login');
      }
    }
  }, [user, loading, router]);

  if (loading) {
    return (
      <div className='loading'>
        <div className='spinner'></div>
        <p>Loading...</p>
      </div>
    );
  }

  return null;
}
