import { redirect } from 'next/navigation';
import { getServerSession } from '@/lib/auth';
import RegisterWrapper from '@/components/RegisterWrapper';

export default async function RegisterPage() {
  const user = await getServerSession();

  // If user is already logged in, redirect to dashboard
  if (user) {
    redirect('/dashboard');
  }

  return <RegisterWrapper />;
}
