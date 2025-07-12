import React from 'react';
import '@/globals.css';
import { Inter } from 'next/font/google';
import { AuthProvider } from '@/app/providers/AuthProvider';
import { ThemeProvider } from '@/app/providers/ThemeProvider';
import ClientHeader from '@/components/ClientHeader';
import ConfigLogger from '@/components/ConfigLogger';
import { getServerSession } from '@/lib/auth';
import type { Metadata, Viewport } from 'next';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Gibster - Gibney Calendar Sync',
  description:
    'Sync your Gibney dance studio bookings with your personal calendar. Never miss a dance class with automatic calendar integration.',
  keywords: [
    'Gibney',
    'dance studio',
    'calendar sync',
    'dance classes',
    'booking sync',
    'calendar integration',
  ],
  authors: [{ name: 'Gibster' }],
  creator: 'Gibster',
  publisher: 'Gibster',
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_FRONTEND_URL || 'https://gibster.app'
  ),
  openGraph: {
    title: 'Gibster - Gibney Calendar Sync',
    description:
      'Sync your Gibney dance studio bookings with your personal calendar. Never miss a dance class.',
    url: '/',
    siteName: 'Gibster',
    type: 'website',
    locale: 'en_US',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'Gibster - Dance Calendar Sync',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Gibster - Gibney Calendar Sync',
    description:
      'Sync your Gibney dance studio bookings with your personal calendar.',
    images: ['/twitter-image.png'],
    creator: '@gibster',
    site: '@gibster',
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  alternates: {
    canonical: '/',
  },
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#ffffff' },
    { media: '(prefers-color-scheme: dark)', color: '#000000' },
  ],
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
