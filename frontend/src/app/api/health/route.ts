import { NextResponse } from 'next/server';
import { getSafeConfig } from '@/lib/config';

export async function GET() {
  const config = getSafeConfig();

  return NextResponse.json({
    status: 'healthy',
    service: 'gibster-frontend',
    version: config.version,
    timestamp: new Date().toISOString(),
    config: {
      environment: config.environment,
      apiBaseUrl: config.api.baseUrl,
      isProduction: config.api.isProduction,
      nodeEnv: config.build.nodeEnv,
    },
  });
}
