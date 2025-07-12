import { redirect } from 'next/navigation';
import { getServerSession } from '@/lib/auth';
import RegisterWrapper from '@/components/RegisterWrapper';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Sign Up - Gibster',
  description:
    'Create your Gibster account to start syncing your Gibney dance studio bookings',
  openGraph: {
    title: 'Sign Up - Gibster',
    description: 'Create an account to sync your dance studio bookings',
  },
  robots: {
    index: false,
    follow: true,
  },
};

export default async function RegisterPage() {
  const user = await getServerSession();

  // If user is already logged in, redirect to dashboard
  if (user) {
    redirect('/dashboard');
  }

  return <RegisterWrapper />;
}
