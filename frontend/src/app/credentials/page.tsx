import { redirect } from 'next/navigation';
import { getServerSession } from '@/lib/auth';
import Credentials from '@/components/Credentials';

export default async function CredentialsPage() {
  const user = await getServerSession();

  // Server-side authentication check
  if (!user) {
    redirect('/login');
  }

  return <Credentials user={user} />;
}
