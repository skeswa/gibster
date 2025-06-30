import React from 'react';
import Link from 'next/link';
import LogoutButton from '@/components/LogoutButton';
import { Button } from '@/components/ui/button';
import { ThemeToggle } from '@/components/ThemeToggle';
import { User, Settings, LayoutDashboard } from 'lucide-react';
import type { User as UserType } from '@/lib/auth';

interface ServerHeaderProps {
  user: UserType | null;
}

export default function ServerHeader({ user }: ServerHeaderProps) {
  return (
    <header className='sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60'>
      <div className='container flex h-16 items-center'>
        <div className='mr-4 flex'>
          <Link href='/' className='mr-6 flex items-center space-x-2'>
            <span className='text-2xl font-bold bg-gradient-to-r from-violet-600 to-purple-600 bg-clip-text text-transparent'>
              Gibster
            </span>
          </Link>
        </div>

        <div className='flex flex-1 items-center justify-end space-x-4'>
          <ThemeToggle />

          {user ? (
            <>
              <div className='flex items-center space-x-2 text-sm text-muted-foreground'>
                <User className='h-4 w-4' />
                <span className='hidden sm:inline-block'>{user.email}</span>
              </div>

              <div className='flex items-center space-x-2'>
                <Button variant='ghost' size='sm' asChild>
                  <Link href='/dashboard'>
                    <LayoutDashboard className='h-4 w-4 mr-2' />
                    Dashboard
                  </Link>
                </Button>

                <Button variant='ghost' size='sm' asChild>
                  <Link href='/credentials'>
                    <Settings className='h-4 w-4 mr-2' />
                    Settings
                  </Link>
                </Button>

                <LogoutButton />
              </div>
            </>
          ) : (
            <>
              <Button variant='ghost' size='sm' asChild>
                <Link href='/login'>Login</Link>
              </Button>
              <Button size='sm' asChild>
                <Link href='/register'>Sign Up</Link>
              </Button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
