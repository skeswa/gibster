import { redirect } from 'next/navigation';
import { getServerSession } from '@/lib/auth';

export default async function HomePage() {
  const user = await getServerSession();

  // Server-side redirect based on authentication status
  if (user) {
    redirect('/dashboard');
  } else {
    redirect('/login');
  }
}
