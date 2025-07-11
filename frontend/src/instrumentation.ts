/**
 * Next.js instrumentation file
 * Runs once when the server starts
 */

export async function register() {
  if (process.env.NEXT_RUNTIME === 'nodejs') {
    // Server startup logging
    console.log('=' + '='.repeat(59));
    console.log('GIBSTER FRONTEND SERVER STARTUP');
    console.log('=' + '='.repeat(59));
    console.log(`Node Version: ${process.version}`);
    console.log(`Environment: ${process.env.NODE_ENV || 'development'}`);
    console.log(
      `API Base URL: ${process.env.NEXT_PUBLIC_API_BASE || 'Not configured'}`
    );
    console.log(
      `Server API URL: ${process.env.API_BASE_URL || 'Using NEXT_PUBLIC_API_BASE'}`
    );
    console.log(`Port: ${process.env.PORT || '3000'}`);
    console.log('=' + '='.repeat(59));
  }
}
