'use client';

import * as React from 'react';
import { useTheme } from 'next-themes';
import { Moon, Sun, Monitor } from 'lucide-react';
import { Button } from '@/components/ui/button';

export function ThemeDropdown() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = React.useState(false);
  const [isOpen, setIsOpen] = React.useState(false);

  // Avoid hydration mismatch
  React.useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return null;
  }

  const toggleDropdown = () => setIsOpen(!isOpen);

  const handleThemeChange = (newTheme: string) => {
    setTheme(newTheme);
    setIsOpen(false);
  };

  return (
    <div className='relative'>
      <Button
        variant='ghost'
        size='sm'
        onClick={toggleDropdown}
        className='h-9 w-9 p-0'
        aria-label='Toggle theme'
      >
        <Sun className='h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0' />
        <Moon className='absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100' />
        <span className='sr-only'>Toggle theme</span>
      </Button>

      {isOpen && (
        <div className='absolute right-0 mt-2 w-36 rounded-md border bg-popover p-1 shadow-md'>
          <button
            onClick={() => handleThemeChange('light')}
            className='flex w-full items-center rounded-sm px-2 py-1.5 text-sm hover:bg-accent hover:text-accent-foreground'
          >
            <Sun className='mr-2 h-4 w-4' />
            Light
          </button>
          <button
            onClick={() => handleThemeChange('dark')}
            className='flex w-full items-center rounded-sm px-2 py-1.5 text-sm hover:bg-accent hover:text-accent-foreground'
          >
            <Moon className='mr-2 h-4 w-4' />
            Dark
          </button>
          <button
            onClick={() => handleThemeChange('system')}
            className='flex w-full items-center rounded-sm px-2 py-1.5 text-sm hover:bg-accent hover:text-accent-foreground'
          >
            <Monitor className='mr-2 h-4 w-4' />
            System
          </button>
        </div>
      )}
    </div>
  );
}
