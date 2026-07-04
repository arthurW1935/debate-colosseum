'use client';
import { useEffect, useState } from 'react';
import { usePathname } from 'next/navigation';
import { isLoggedIn } from '@/lib/auth';
import LoginButton from './LoginButton';

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const [authed, setAuthed] = useState<boolean | null>(null);
  const pathname = usePathname();

  useEffect(() => {
    setAuthed(isLoggedIn());
  }, []);

  if (pathname === '/auth/callback') {
    return <>{children}</>;
  }

  if (authed === null) {
    return <div className="animate-pulse flex space-x-4"><div className="rounded-full bg-white/5 h-10 w-10"></div></div>;
  }

  if (!authed) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center z-10 relative">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-indigo-600/20 border border-indigo-500/30 mb-5 text-3xl">
          🔒
        </div>
        <h2 className="text-2xl font-bold text-white mb-2">Sign in to Debate Colosseum</h2>
        <p className="text-slate-400 mb-8 max-w-sm">Join to create debates and get insights from our AI agents.</p>
        <LoginButton />
      </div>
    );
  }

  return <>{children}</>;
}
