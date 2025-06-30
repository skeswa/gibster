import React from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { ArrowLeft, Shield, HelpCircle } from 'lucide-react';
import CredentialsForm from './CredentialsForm';

interface User {
  id: string;
  email: string;
  [key: string]: any;
}

interface CredentialsProps {
  user: User;
}

const Credentials: React.FC<CredentialsProps> = ({ user }) => {
  return (
    <div className='max-w-4xl mx-auto space-y-6'>
      <div className='flex items-center justify-between'>
        <h1 className='text-3xl font-bold'>Manage Credentials</h1>
        <Button variant='outline' asChild>
          <Link href='/dashboard'>
            <ArrowLeft className='mr-2 h-4 w-4' />
            Back to Dashboard
          </Link>
        </Button>
      </div>
      <Alert>
        <Shield className='h-4 w-4' />
        <AlertDescription>
          <strong>Privacy Notice:</strong> Your Gibney credentials are encrypted
          and stored securely. They are only used to sync your bookings and are
          never shared with third parties.
        </AlertDescription>
      </Alert>

      {/* Client component for interactive form */}
      <CredentialsForm />

      <Card>
        <CardHeader>
          <CardTitle className='flex items-center gap-2'>
            <HelpCircle className='h-5 w-5' />
            How it works
          </CardTitle>
        </CardHeader>
        <CardContent className='space-y-4'>
          <ol className='list-decimal list-inside space-y-2 text-sm text-muted-foreground'>
            <li>Enter your Gibney credentials here</li>
            <li>Gibster will automatically sync your bookings every 2 hours</li>
            <li>Your calendar feed will be updated with the latest bookings</li>
            <li>
              Subscribe to your calendar feed in your favorite calendar app
            </li>
          </ol>

          <div className='pt-4 border-t'>
            <p className='text-sm'>
              <strong>Need help?</strong> Visit{' '}
              <a
                href='https://gibney.my.site.com/'
                target='_blank'
                rel='noopener noreferrer'
                className='text-primary hover:underline'
              >
                gibney.my.site.com
              </a>{' '}
              to check your login credentials or reset your password.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Credentials;
