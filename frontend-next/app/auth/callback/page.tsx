'use client';
import { useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { saveToken } from '@/lib/auth';
import { Loader2 } from 'lucide-react';

function CallbackInner() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const token = searchParams?.get('token');
    if (token) {
      saveToken(token);
    }
    router.push('/app');
  }, [router, searchParams]);

  return (
    <div className="executive-shell flex min-h-screen items-center justify-center text-[var(--text-primary)]">
      <Loader2 className="h-8 w-8 animate-spin text-[var(--accent)]" />
    </div>
  );
}

export default function AuthCallback() {
  return (
    <Suspense fallback={<div className="executive-shell min-h-screen" />}>
      <CallbackInner />
    </Suspense>
  );
}
