'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { LogOut } from 'lucide-react';

export default function LogoutButton() {
  const router = useRouter();

  const handleLogout = () => {
    // Remove token from localStorage
    localStorage.removeItem('token');

    // Remove token from cookies for server-side
    document.cookie = 'token=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT;';

    // Redirect to login
    router.push('/login');

    // Force a hard refresh to clear any cached data
    window.location.reload();
  };

  return (
    <Button variant='outline' size='sm' onClick={handleLogout}>
      <LogOut className='h-4 w-4 mr-2' />
      Logout
    </Button>
  );
}
