import { redirect } from 'next/navigation';
import { getServerSession } from '@/lib/auth';
import Dashboard from '@/components/Dashboard';

export default async function DashboardPage() {
  const user = await getServerSession();

  // Server-side authentication check
  if (!user) {
    redirect('/login');
  }

  return <Dashboard user={user} />;
}
