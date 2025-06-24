'use client';

import React from 'react';
import { redirect } from 'next/navigation';
import Login from '../../components/Login';
import { useAuth } from '../providers/AuthProvider';

export default function LoginPage() {
  const { user, login } = useAuth();

  if (user) {
    redirect('/dashboard');
  }

  return <Login onLogin={login} />;
}
