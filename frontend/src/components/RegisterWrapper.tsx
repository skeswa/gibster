'use client';

import React from 'react';
import Register from '@/components/Register';
import { useAuth } from '@/app/providers/AuthProvider';

export default function RegisterWrapper() {
  const { login } = useAuth();

  return <Register onLogin={login} />;
}
