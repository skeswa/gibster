'use client';

import React from 'react';
import { redirect } from 'next/navigation';
import Credentials from '@/components/Credentials';
import { useAuth } from '@/app/providers/AuthProvider';

export default function CredentialsPage() {
  const { user } = useAuth();

  if (!user) {
    redirect('/login');
  }

  return <Credentials user={user} />;
}
