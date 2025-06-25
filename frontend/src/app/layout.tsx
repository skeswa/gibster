import React from 'react';
import '@/index.css';
import { AuthProvider } from '@/app/providers/AuthProvider';
import ServerHeader from '@/components/ServerHeader';
import { getServerSession } from '@/lib/auth';

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
    <html lang='en'>
      <head>
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
          <AuthProvider initialUser={user}>
            <div className='App'>
              <ServerHeader user={user} />
              <main className='main-content'>{children}</main>
            </div>
          </AuthProvider>
        </div>
      </body>
    </html>
  );
}
