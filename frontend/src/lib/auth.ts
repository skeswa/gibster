import { cookies } from 'next/headers';

// Server-side API calls use internal/service URLs, client-side uses public URLs
const API_BASE =
  process.env.API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_BASE ||
  'http://localhost:8000';

export interface User {
  id: string;
  email: string;
  [key: string]: any;
}

export async function getServerSession(): Promise<User | null> {
  const cookieStore = await cookies();
  const token = cookieStore.get('token')?.value;

  if (!token) {
    return null;
  }

  try {
    const response = await fetch(`${API_BASE}/api/v1/user/profile`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      // Add cache control for better performance
      next: { revalidate: 300 }, // 5 minutes
    });

    if (response.ok) {
      const userData: User = await response.json();
      return userData;
    } else {
      // Token is invalid, should be removed
      return null;
    }
  } catch (error) {
    console.error('Error fetching user profile:', error);
    return null;
  }
}

export function isAuthenticated(user: User | null): user is User {
  return user !== null;
}
