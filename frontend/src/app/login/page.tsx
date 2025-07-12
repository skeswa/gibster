import { redirect } from 'next/navigation';
import { getServerSession } from '@/lib/auth';
import LoginWrapper from '@/components/LoginWrapper';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Login - Gibster',
  description:
    'Sign in to your Gibster account to sync your Gibney dance studio bookings',
  openGraph: {
    title: 'Login - Gibster',
    description: 'Sign in to sync your dance studio bookings',
  },
  robots: {
    index: false,
    follow: true,
  },
};

export default async function LoginPage() {
  const user = await getServerSession();

  // If user is already logged in, redirect to dashboard
  if (user) {
    redirect('/dashboard');
  }

  return <LoginWrapper />;
}
