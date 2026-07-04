'use client';

import { useEffect, useState } from 'react';
import { ThemeMode } from './ThemeToggle';

const THEME_KEY = 'debate_colosseum_theme';

export function useThemeMode() {
  const [theme, setTheme] = useState<ThemeMode>('light');

  useEffect(() => {
    const saved = localStorage.getItem(THEME_KEY);
    if (saved === 'light' || saved === 'dark') setTheme(saved);
  }, []);

  const toggleTheme = () => {
    setTheme(current => {
      const next = current === 'light' ? 'dark' : 'light';
      localStorage.setItem(THEME_KEY, next);
      return next;
    });
  };

  return { theme, toggleTheme };
}
