import React from 'react';
import '@/globals.css';
import { Inter } from 'next/font/google';
import { AuthProvider } from '@/app/providers/AuthProvider';
import { ThemeProvider } from '@/app/providers/ThemeProvider';
import ServerHeader from '@/components/ServerHeader';
import { getServerSession } from '@/lib/auth';

const inter = Inter({ subsets: ['latin'] });

export const metadata = {
  title: 'Gibster - Gibney Calendar Sync',
  description:
    'Gibster - Sync your Gibney dance studio bookings with your calendar',
};

export const viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: '#000000',
};

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // Get user session on the server
  const user = await getServerSession();

  return (
    <html lang='en' className={inter.className} suppressHydrationWarning>
      <body className='min-h-screen bg-background'>
        <ThemeProvider
          attribute='class'
          defaultTheme='system'
          enableSystem
          disableTransitionOnChange
        >
          <AuthProvider initialUser={user}>
            <div className='min-h-screen'>
              <ServerHeader user={user} />
              <main className='container mx-auto px-4 py-8'>{children}</main>
            </div>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
