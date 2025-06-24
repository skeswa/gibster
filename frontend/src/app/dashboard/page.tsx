'use client';

import React from 'react';
import { redirect } from 'next/navigation';
import Dashboard from '../../components/Dashboard';
import { useAuth } from '../providers/AuthProvider';

export default function DashboardPage() {
  const { user } = useAuth();

  if (!user) {
    redirect('/login');
  }

  return <Dashboard user={user} />;
}
