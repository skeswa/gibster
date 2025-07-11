import React from 'react';
import '@/globals.css';
import { Inter } from 'next/font/google';
import { AuthProvider } from '@/app/providers/AuthProvider';
import { ThemeProvider } from '@/app/providers/ThemeProvider';
import ClientHeader from '@/components/ClientHeader';
import ConfigLogger from '@/components/ConfigLogger';
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
            <ConfigLogger />
            {children}
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
