import { MetadataRoute } from 'next';

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: 'Gibster - Gibney Calendar Sync',
    short_name: 'Gibster',
    description:
      'Sync your Gibney dance studio bookings with your personal calendar. Never miss a dance class with automatic calendar integration.',
    start_url: '/',
    display: 'standalone',
    background_color: '#0f172a',
    theme_color: '#3b82f6',
    orientation: 'portrait-primary',
    categories: ['productivity', 'lifestyle', 'dance'],
    icons: [
      {
        src: '/icon.png',
        sizes: '512x512',
        type: 'image/png',
        purpose: 'any',
      },
      {
        src: '/icon.png',
        sizes: '512x512',
        type: 'image/png',
        purpose: 'maskable',
      },
      {
        src: '/apple-icon.png',
        sizes: '180x180',
        type: 'image/png',
      },
      {
        src: '/favicon.ico',
        sizes: '32x32',
        type: 'image/x-icon',
      },
    ],
    shortcuts: [
      {
        name: 'Dashboard',
        short_name: 'Dashboard',
        description: 'View your calendar sync dashboard',
        url: '/dashboard',
        icons: [{ src: '/icon.png', sizes: '96x96' }],
      },
      {
        name: 'Update Credentials',
        short_name: 'Credentials',
        description: 'Update your Gibney credentials',
        url: '/credentials',
        icons: [{ src: '/icon.png', sizes: '96x96' }],
      },
    ],
    screenshots: [
      {
        src: '/og-image.png',
        type: 'image/png',
        sizes: '1200x630',
        form_factor: 'wide',
        label: 'Gibster Homepage',
      },
    ],
    related_applications: [],
    prefer_related_applications: false,
  };
}
