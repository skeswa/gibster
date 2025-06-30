'use client';

import { useTheme } from 'next-themes';
import { useEffect, useState } from 'react';

export function useThemeState() {
  const { theme, setTheme, systemTheme, resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Get the actual theme being used (resolved theme accounts for system preference)
  const currentTheme = mounted ? resolvedTheme : undefined;

  // Check if dark mode is active
  const isDarkMode = currentTheme === 'dark';

  return {
    theme,
    setTheme,
    systemTheme,
    currentTheme,
    isDarkMode,
    mounted,
  };
}
