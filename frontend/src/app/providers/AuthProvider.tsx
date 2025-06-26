'use client';

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from 'react';
import { useRouter } from 'next/navigation';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || '';

interface User {
  id: string;
  email: string;
  [key: string]: any;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (token: string, userData: User) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({
  children,
  initialUser = null,
}: {
  children: ReactNode;
  initialUser?: User | null;
}) {
  const [user, setUser] = useState<User | null>(initialUser);
  const [loading, setLoading] = useState<boolean>(false);
  const router = useRouter();

  useEffect(() => {
    // Only check auth status if we don't have initial user data
    if (initialUser === null) {
      checkAuthStatus();
    }
  }, [initialUser]);

  const checkAuthStatus = async (): Promise<void> => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        // Verify token with server
        const response = await fetch(`${API_BASE}/api/v1/user/profile`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (response.ok) {
          const userData: User = await response.json();
          setUser(userData);
        } else {
          throw new Error('Token invalid');
        }
      } catch (error) {
        localStorage.removeItem('token');
        // Also remove from cookies
        document.cookie =
          'token=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT;';
        setUser(null);
      } finally {
        setLoading(false);
      }
    } else {
      setLoading(false);
    }
  };

  const login = (token: string, userData: User): void => {
    // Store in localStorage for client-side
    localStorage.setItem('token', token);

    // Store in cookies for server-side
    document.cookie = `token=${token}; Path=/; Max-Age=${7 * 24 * 60 * 60}; SameSite=Strict; Secure=${process.env.NODE_ENV === 'production'}`;

    setUser(userData);

    // Navigate to dashboard after successful login
    router.push('/dashboard');
  };

  const logout = (): void => {
    localStorage.removeItem('token');

    // Remove token from cookies
    document.cookie = 'token=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT;';

    setUser(null);
    router.push('/login');

    // Force a hard refresh to clear any cached data
    window.location.reload();
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
