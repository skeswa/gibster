# Theme Implementation Guide

This document describes the dark mode theme implementation for the Gibster frontend application.

## Overview

The theme system is built using:
- **next-themes**: For theme management and persistence
- **Tailwind CSS**: With class-based dark mode (`darkMode: ["class"]`)
- **CSS Variables**: For dynamic color theming

## Components

### ThemeProvider
Located in `/src/app/providers/ThemeProvider.tsx`

A client component that wraps the entire application and provides theme context.

**Props:**
- `attribute`: Set to `'class'` to add the theme class to the HTML element
- `defaultTheme`: Set to `'system'` to respect user's OS preference by default
- `enableSystem`: Enables automatic theme switching based on system preference
- `disableTransitionOnChange`: Prevents flashing during theme changes

### Theme Toggle Components

#### ThemeToggle
Located in `/src/components/ThemeToggle.tsx`

A button group component showing three buttons for light, dark, and system themes.

#### ThemeDropdown
Located in `/src/components/ThemeDropdown.tsx`

A dropdown menu component with a single button that toggles between themes.

#### ThemeSelect
Located in `/src/components/ThemeSelect.tsx`

A native select element for theme selection (most accessible option).

### Custom Hook

#### useThemeState
Located in `/src/hooks/useThemeState.ts`

Provides easy access to theme state and utilities:
```typescript
const { theme, setTheme, currentTheme, isDarkMode, mounted } = useThemeState();
```

## Usage

### Basic Theme Toggle
```tsx
import { ThemeToggle } from '@/components/ThemeToggle';

function Header() {
  return (
    <header>
      <ThemeToggle />
    </header>
  );
}
```

### Conditional Rendering Based on Theme
```tsx
import { useThemeState } from '@/hooks/useThemeState';

function Component() {
  const { isDarkMode, mounted } = useThemeState();
  
  if (!mounted) return null; // Avoid hydration mismatch
  
  return (
    <div>
      {isDarkMode ? 'Dark mode active' : 'Light mode active'}
    </div>
  );
}
```

### Theme-Aware Styling
```tsx
// Using Tailwind's dark: modifier
<div className="bg-white dark:bg-gray-900">
  <p className="text-black dark:text-white">Theme-aware text</p>
</div>
```

## CSS Variables

The theme system uses CSS variables defined in `/src/globals.css`:

```css
:root {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  /* ... other variables ... */
}

.dark {
  --background: 222.2 84% 4.9%;
  --foreground: 210 40% 98%;
  /* ... other variables ... */
}
```

These variables are used by Tailwind's color system (configured in `tailwind.config.js`).

## Features

1. **Automatic persistence**: Theme choice is saved to localStorage
2. **System preference detection**: Respects OS dark/light mode settings
3. **No flash on reload**: `suppressHydrationWarning` prevents theme flashing
4. **Smooth transitions**: CSS transitions for theme changes (can be disabled)
5. **TypeScript support**: Full type safety with next-themes

## Demo Page

Visit `/theme-demo` to see all themed components in action.

## Best Practices

1. Always check `mounted` state before rendering theme-dependent content
2. Use the `dark:` Tailwind modifier for conditional dark mode styles
3. Prefer CSS variables for colors to ensure consistency
4. Test both light and dark modes when developing new components