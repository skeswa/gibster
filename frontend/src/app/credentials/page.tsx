import { redirect } from 'next/navigation';
import { getServerSession } from '@/lib/auth';
import Credentials from '@/components/Credentials';
import AuthenticatedLayout from '@/components/AuthenticatedLayout';

export default async function CredentialsPage() {
  const user = await getServerSession();

  // Server-side authentication check
  if (!user) {
    redirect('/login');
  }

  return (
    <AuthenticatedLayout>
      <Credentials user={user} />
    </AuthenticatedLayout>
  );
}
