import { redirect } from 'next/navigation';
import { getServerSession } from '@/lib/auth';
import Dashboard from '@/components/Dashboard';
import AuthenticatedLayout from '@/components/AuthenticatedLayout';
import { cookies } from 'next/headers';

// Server-side API calls use internal/service URLs, client-side uses public URLs
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Booking {
  id: string;
  name: string;
  start_time: string;
  end_time: string;
  studio: string;
  location: string;
  status: string;
  price?: number;
  record_url: string;
  last_seen: string;
}

interface CalendarResponse {
  calendar_url: string;
  calendar_uuid: string;
}

async function getDashboardData(token: string) {
  try {
    // Fetch bookings and calendar URL in parallel
    const [bookingsResponse, calendarResponse] = await Promise.all([
      fetch(`${API_BASE}/api/v1/user/bookings`, {
        headers: { Authorization: `Bearer ${token}` },
        cache: 'no-store', // Always fetch fresh data
      }),
      fetch(`${API_BASE}/api/v1/user/calendar_url`, {
        headers: { Authorization: `Bearer ${token}` },
        cache: 'no-store',
      }),
    ]);

    const bookings: Booking[] = bookingsResponse.ok
      ? await bookingsResponse.json()
      : [];
    const calendarData: CalendarResponse | null = calendarResponse.ok
      ? await calendarResponse.json()
      : null;

    return {
      bookings,
      calendarUrl: calendarData?.calendar_url || '',
    };
  } catch (error) {
    console.error('Failed to fetch dashboard data:', error);
    return {
      bookings: [],
      calendarUrl: '',
    };
  }
}

export default async function DashboardPage() {
  const user = await getServerSession();

  // Server-side authentication check
  if (!user) {
    redirect('/login');
  }

  // Get token from cookies for server-side API calls
  const cookieStore = await cookies();
  const token = cookieStore.get('token')?.value;

  if (!token) {
    redirect('/login');
  }

  // Fetch dashboard data server-side
  const { bookings, calendarUrl } = await getDashboardData(token);

  return (
    <AuthenticatedLayout>
      <Dashboard user={user} bookings={bookings} calendarUrl={calendarUrl} />
    </AuthenticatedLayout>
  );
}
