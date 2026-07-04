'use client';

import { Moon, Sun } from 'lucide-react';

export type ThemeMode = 'light' | 'dark';

interface ThemeToggleProps {
  theme: ThemeMode;
  onToggle: () => void;
}

export default function ThemeToggle({ theme, onToggle }: ThemeToggleProps) {
  const isDark = theme === 'dark';

  return (
    <button
      type="button"
      onClick={onToggle}
      className="inline-flex items-center gap-2 rounded-full border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-xs font-semibold text-[var(--text-primary)] shadow-sm transition hover:-translate-y-0.5 hover:border-[var(--border-strong)]"
      aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode`}
    >
      {isDark ? <Sun className="h-3.5 w-3.5" /> : <Moon className="h-3.5 w-3.5" />}
      {isDark ? 'Light' : 'Dark'}
    </button>
  );
}
