'use client';

import React from 'react';
import Login from '@/components/Login';
import { useAuth } from '@/app/providers/AuthProvider';

export default function LoginWrapper() {
  const { login } = useAuth();

  return <Login onLogin={login} />;
}
