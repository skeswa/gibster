'use client';

import * as React from 'react';
import { useTheme } from 'next-themes';
import { Moon, Sun, Monitor } from 'lucide-react';
import { Button } from '@/components/ui/button';

export function ThemeToggle() {
  const { theme, setTheme, systemTheme } = useTheme();
  const [mounted, setMounted] = React.useState(false);

  // Avoid hydration mismatch
  React.useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return null;
  }

  const currentTheme = theme === 'system' ? systemTheme : theme;

  return (
    <div className='flex items-center gap-1'>
      <Button
        variant='ghost'
        size='sm'
        onClick={() => setTheme('light')}
        className={theme === 'light' ? 'bg-accent' : ''}
        aria-label='Light mode'
      >
        <Sun className='h-4 w-4' />
      </Button>
      <Button
        variant='ghost'
        size='sm'
        onClick={() => setTheme('dark')}
        className={theme === 'dark' ? 'bg-accent' : ''}
        aria-label='Dark mode'
      >
        <Moon className='h-4 w-4' />
      </Button>
      <Button
        variant='ghost'
        size='sm'
        onClick={() => setTheme('system')}
        className={theme === 'system' ? 'bg-accent' : ''}
        aria-label='System theme'
      >
        <Monitor className='h-4 w-4' />
      </Button>
    </div>
  );
}
