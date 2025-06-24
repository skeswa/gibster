import React from 'react';
import Link from 'next/link';

interface User {
  id: string;
  email: string;
  [key: string]: any;
}

interface HeaderProps {
  user: User | null;
  onLogout: () => void;
}

const Header: React.FC<HeaderProps> = ({ user, onLogout }) => {
  return (
    <header className='header'>
      <h1>Gibster</h1>

      <nav>
        {user ? (
          <>
            <span className='user-info'>Welcome, {user.email}</span>
            <Link href='/dashboard' className='btn btn-secondary'>
              Dashboard
            </Link>
            <Link href='/credentials' className='btn btn-secondary'>
              Settings
            </Link>
            <button onClick={onLogout} className='btn btn-danger'>
              Logout
            </button>
          </>
        ) : (
          <>
            <Link href='/login' className='btn btn-primary'>
              Login
            </Link>
            <Link href='/register' className='btn btn-secondary'>
              Register
            </Link>
          </>
        )}
      </nav>
    </header>
  );
};

export default Header;
