import { redirect } from 'next/navigation';
import { getServerSession } from '@/lib/auth';
import Credentials from '@/components/Credentials';
import AuthenticatedLayout from '@/components/AuthenticatedLayout';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Gibney Credentials - Gibster',
  description:
    'Manage your Gibney account credentials for automatic booking synchronization',
  robots: {
    index: false,
    follow: false,
  },
};

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
