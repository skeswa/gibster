import { redirect } from 'next/navigation';
import { getServerSession } from '@/lib/auth';
import LoginWrapper from '@/components/LoginWrapper';

export default async function LoginPage() {
  const user = await getServerSession();

  // If user is already logged in, redirect to dashboard
  if (user) {
    redirect('/dashboard');
  }

  return <LoginWrapper />;
}
