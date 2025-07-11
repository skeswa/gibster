/**
 * Frontend configuration management
 */

// Environment configuration
export const config = {
  api: {
    baseUrl: process.env.NEXT_PUBLIC_API_URL || '',
    // Server-side rendering uses the same variable
    serverBaseUrl: process.env.NEXT_PUBLIC_API_URL || '',
  },
  environment: process.env.NODE_ENV || 'development',
  version: '1.0.0',
};

/**
 * Get safe configuration for logging (no sensitive data)
 */
export function getSafeConfig() {
  return {
    environment: config.environment,
    version: config.version,
    api: {
      baseUrl: config.api.baseUrl || 'Not configured',
      isProduction: config.environment === 'production',
    },
    build: {
      nodeEnv: process.env.NODE_ENV,
      // Next.js specific
      isServer: typeof window === 'undefined',
    },
  };
}

/**
 * Log configuration summary
 * Only logs in development mode to avoid exposing config in production console
 */
export function logConfiguration() {
  if (config.environment !== 'production') {
    const safeConfig = getSafeConfig();

    console.group('🚀 Gibster Frontend Configuration');
    console.log('Environment:', safeConfig.environment);
    console.log('Version:', safeConfig.version);
    console.log('API Base URL:', safeConfig.api.baseUrl);
    console.log('Is Server:', safeConfig.build.isServer);

    // Client-side only info
    if (!safeConfig.build.isServer && typeof window !== 'undefined') {
      console.log('User Agent:', window.navigator.userAgent);
      console.log('Screen:', `${window.screen.width}x${window.screen.height}`);
      console.log('Viewport:', `${window.innerWidth}x${window.innerHeight}`);
    }

    console.groupEnd();
  }
}

// Export for use in API client
export const API_BASE = config.api.baseUrl;
