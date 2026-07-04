'use client';
import { useEffect, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { isLoggedIn } from '@/lib/auth';
import { Loader2 } from 'lucide-react';

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const [authed, setAuthed] = useState<boolean | null>(null);
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    const loggedIn = isLoggedIn();
    setAuthed(loggedIn);
    if (!loggedIn && pathname !== '/auth/callback') {
      router.replace('/');
    }
  }, [pathname, router]);

  if (pathname === '/auth/callback') {
    return <>{children}</>;
  }

  if (authed === null) {
    return (
      <div className="executive-shell flex min-h-screen items-center justify-center text-[var(--text-secondary)]">
        <Loader2 className="h-5 w-5 animate-spin text-[var(--accent)]" />
      </div>
    );
  }

  if (!authed) {
    return (
      <div className="executive-shell flex min-h-screen items-center justify-center text-center text-[var(--text-secondary)]">
        <div className="glass-panel rounded-3xl px-6 py-5 text-sm">
          Redirecting to sign in...
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
