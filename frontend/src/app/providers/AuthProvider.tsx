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

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const router = useRouter();

  useEffect(() => {
    checkAuthStatus();
  }, []);

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
        setUser(null);
      } finally {
        setLoading(false);
      }
    } else {
      setLoading(false);
    }
  };

  const login = (token: string, userData: User): void => {
    localStorage.setItem('token', token);
    setUser(userData);
  };

  const logout = (): void => {
    localStorage.removeItem('token');
    setUser(null);
    router.push('/login');
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
