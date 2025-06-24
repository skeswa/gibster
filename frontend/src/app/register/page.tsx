'use client';

import React from 'react';
import { redirect } from 'next/navigation';
import Register from '@/components/Register';
import { useAuth } from '@/app/providers/AuthProvider';

export default function RegisterPage() {
  const { user, login } = useAuth();

  if (user) {
    redirect('/dashboard');
  }

  return <Register onLogin={login} />;
}
