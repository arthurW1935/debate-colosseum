'use client';
import { useEffect, useState } from 'react';

interface RateLimitBannerProps {
  retryAfter: number;
  onDismiss: () => void;
}

export function RateLimitBanner({ retryAfter, onDismiss }: RateLimitBannerProps) {
  const [timeLeft, setTimeLeft] = useState(retryAfter);

  useEffect(() => {
    setTimeLeft(retryAfter);
  }, [retryAfter]);

  useEffect(() => {
    if (timeLeft <= 0) {
      onDismiss();
      return;
    }
    const timer = setInterval(() => {
      setTimeLeft((prev) => Math.max(0, prev - 1));
    }, 1000);
    return () => clearInterval(timer);
  }, [timeLeft, onDismiss]);

  if (timeLeft <= 0) return null;

  return (
    <div className="fixed top-6 left-1/2 -translate-x-1/2 z-50 transition-all duration-300 ease-out">
      <div className="bg-amber-950/90 border border-amber-500/50 text-amber-200 px-6 py-4 rounded-xl shadow-2xl shadow-amber-900/20 flex items-center gap-4 backdrop-blur-md">
        <div className="bg-amber-500/20 p-2 rounded-full">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-amber-400 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <div>
          <p className="font-semibold text-sm tracking-wide">You're going too fast!</p>
          <p className="text-xs text-amber-300/80 mt-0.5">Try again in <span className="font-mono font-bold text-amber-400">{timeLeft}</span> seconds</p>
        </div>
      </div>
    </div>
  );
}
