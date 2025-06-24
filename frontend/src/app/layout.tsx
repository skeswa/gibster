'use client';

import React from 'react';
import '@/index.css';
import { AuthProvider } from '@/app/providers/AuthProvider';
import Header from '@/components/Header';
import { useAuth } from '@/app/providers/AuthProvider';

function AppContent({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();

  return (
    <div className='App'>
      <Header user={user} onLogout={logout} />
      <main className='main-content'>{children}</main>
    </div>
  );
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang='en'>
      <head>
        <meta charSet='utf-8' />
        <meta name='viewport' content='width=device-width, initial-scale=1' />
        <meta name='theme-color' content='#000000' />
        <meta
          name='description'
          content='Gibster - Sync your Gibney dance studio bookings with your calendar'
        />
        <title>Gibster - Gibney Calendar Sync</title>
        <style>{`
          body {
            margin: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
              'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
              sans-serif;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
          }
          
          code {
            font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
              monospace;
          }
        `}</style>
      </head>
      <body>
        <div id='root'>
          <AuthProvider>
            <AppContent>{children}</AppContent>
          </AuthProvider>
        </div>
      </body>
    </html>
  );
}
