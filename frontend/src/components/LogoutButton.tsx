'use client';

import React from 'react';
import { useRouter } from 'next/navigation';

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
    <button onClick={handleLogout} className='btn btn-danger'>
      Logout
    </button>
  );
}
