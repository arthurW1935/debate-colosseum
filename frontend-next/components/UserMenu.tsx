'use client';
import { useState, useEffect } from 'react';
import { getUserFromToken, removeToken } from '@/lib/auth';
import { logoutCurrentSession } from '@/lib/session';
import { LogOut } from 'lucide-react';

export default function UserMenu({ compact = false }: { compact?: boolean }) {
  const [user, setUser] = useState<{ id: string; email: string; name: string } | null>(null);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    setUser(getUserFromToken());
  }, []);

  if (!user) return null;

  const handleLogout = async () => {
    await logoutCurrentSession();
    removeToken();
    window.location.href = '/';
  };

  const initial = (user.name || user.email || 'U').charAt(0);

  return (
    <div className="relative z-50">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`flex w-full items-center gap-2 rounded-2xl border border-[var(--border)] bg-[var(--surface)]/75 text-[var(--text-primary)] shadow-sm transition hover:-translate-y-0.5 hover:bg-[var(--surface)] ${
          compact ? 'h-11 justify-center px-0' : 'px-3 py-2.5'
        }`}
        aria-label="Open user menu"
      >
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[var(--text-primary)] text-xs font-bold uppercase text-[var(--app-bg)]">
          {initial}
        </div>
        {!compact && (
          <div className="min-w-0 text-left">
            <p className="truncate text-xs font-semibold">{user.name || user.email}</p>
            <p className="truncate text-[10px] text-[var(--text-tertiary)]">{user.email}</p>
          </div>
        )}
      </button>

      {isOpen && (
        <div
          className={`absolute bottom-full mb-2 overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--surface)]/95 py-1 shadow-[var(--shadow-card)] backdrop-blur-xl ${
            compact ? 'left-0 w-56' : 'left-0 right-0'
          }`}
        >
          <div className="border-b border-[var(--border)] px-4 py-2">
            <p className="truncate text-xs font-semibold text-[var(--text-primary)]">{user.name || 'Signed in'}</p>
            <p className="truncate text-[10px] text-[var(--text-tertiary)]">{user.email}</p>
          </div>
          <button
            onClick={handleLogout}
            className="flex w-full items-center gap-2 px-4 py-2.5 text-left text-xs font-semibold text-[var(--danger)] transition hover:bg-[var(--danger)]/10"
          >
            <LogOut className="h-3.5 w-3.5" />
            Log out
          </button>
        </div>
      )}
    </div>
  );
}
