import { redirect } from 'next/navigation';
import { getServerSession } from '@/lib/auth';
import LandingPage from './landing-page';

export default async function HomePage() {
  const user = await getServerSession();

  // If authenticated, redirect to dashboard
  if (user) {
    redirect('/dashboard');
  }

  // Otherwise, show the landing page
  return <LandingPage />;
}
