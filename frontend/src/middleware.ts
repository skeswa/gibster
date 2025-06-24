import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Define which paths require authentication
const protectedPaths = ['/dashboard', '/credentials'];
// Define which paths should redirect authenticated users
const authPaths = ['/login', '/register'];

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const token = request.cookies.get('token')?.value;

  // Check if current path is protected
  const isProtectedPath = protectedPaths.some(path =>
    pathname.startsWith(path)
  );
  // Check if current path is auth-related (login/register)
  const isAuthPath = authPaths.some(path => pathname.startsWith(path));

  // If accessing protected route without token, redirect to login
  if (isProtectedPath && !token) {
    const loginUrl = new URL('/login', request.url);
    return NextResponse.redirect(loginUrl);
  }

  // If accessing auth routes with valid token, redirect to dashboard
  if (isAuthPath && token) {
    // We could validate the token here with an API call, but for performance
    // we'll let the server component handle validation
    const dashboardUrl = new URL('/dashboard', request.url);
    return NextResponse.redirect(dashboardUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder files
     */
    '/((?!api|_next/static|_next/image|favicon.ico|public).*)',
  ],
};
