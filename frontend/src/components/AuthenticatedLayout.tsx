import React from 'react';
import ClientHeader from '@/components/ClientHeader';

export default function AuthenticatedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className='min-h-screen'>
      <ClientHeader />
      <main className='container mx-auto px-4 py-8'>{children}</main>
    </div>
  );
}
