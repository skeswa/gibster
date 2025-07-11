'use client';

import { useEffect } from 'react';
import { logConfiguration } from '@/lib/config';

export default function ConfigLogger() {
  useEffect(() => {
    // Log configuration on client-side mount
    // Only in development mode
    if (process.env.NODE_ENV !== 'production') {
      logConfiguration();
    }
  }, []);

  return null; // This component doesn't render anything
}
