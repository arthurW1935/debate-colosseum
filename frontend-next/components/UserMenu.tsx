'use client';
import { useState, useEffect } from 'react';
import { getUserFromToken, removeToken } from '@/lib/auth';

export default function UserMenu() {
  const [user, setUser] = useState<{ id: string; email: string; name: string } | null>(null);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    setUser(getUserFromToken());
  }, []);

  if (!user) return null;

  const handleLogout = () => {
    removeToken();
    window.location.reload();
  };

  return (
    <div className="relative z-50">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 hover:bg-white/10 transition-colors"
      >
        <div className="w-6 h-6 rounded-full bg-indigo-500 text-white flex items-center justify-center text-xs font-bold uppercase">
          {user.name.charAt(0)}
        </div>
        <span className="text-sm font-medium text-slate-200">{user.name}</span>
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-48 rounded-xl bg-[#1a1a24]/90 backdrop-blur-xl border border-white/10 shadow-2xl overflow-hidden py-1">
          <div className="px-4 py-2 border-b border-white/5">
            <p className="text-xs text-slate-400 truncate">{user.email}</p>
          </div>
          <button
            onClick={handleLogout}
            className="w-full text-left px-4 py-2 text-sm text-red-400 hover:bg-white/5 transition-colors"
          >
            Sign Out
          </button>
        </div>
      )}
    </div>
  );
}
