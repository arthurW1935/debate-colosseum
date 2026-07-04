'use client';
import { useState } from 'react';
import { Loader2, Send } from 'lucide-react';
import { submitReview } from '@/lib/api';
import { RunStatus } from '@/types';

interface QueryBoxProps {
  runId: string;
  status: RunStatus;
  onAction: (decision: 'approved' | 'feedback' | 'abandoned', feedbackText?: string) => void;
}

export default function QueryBox({ runId, status, onAction }: QueryBoxProps) {
  const [feedback, setFeedback] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isReview = status === 'awaiting_review';
  const isRunning = status === 'running';

  const sendRefinement = async () => {
    if (!feedback.trim() || !isReview) return;
    setLoading(true);
    setError(null);
    try {
      const text = feedback.trim();
      await submitReview(runId, 'feedback', text);
      onAction('feedback', text);
      setFeedback('');
    } catch (e) {
      setError(String(e));
    }
    setLoading(false);
  };

  return (
    <div className="rounded-[22px] border border-[var(--border)] bg-[var(--surface)]/95 shadow-[var(--shadow-card)] backdrop-blur transition-all duration-200">
      <div className="flex items-center gap-2 p-2">
        <div className="flex-1">
          <textarea
            value={isReview ? feedback : ''}
            onChange={e => setFeedback(e.target.value)}
            disabled={!isReview || loading}
            rows={1}
            placeholder={
              isRunning
                ? 'The debate is live. You can refine the memo when the specialists return.'
                : isReview
                ? 'Ask for a revision, e.g. “make the finance section stricter”'
                : 'This decision is closed'
            }
            onKeyDown={e => {
              if (e.key === 'Enter' && !e.shiftKey && isReview) {
                e.preventDefault();
                sendRefinement();
              }
            }}
            className={`w-full resize-none rounded-2xl border px-3.5 py-2 text-xs leading-5 outline-none transition-all ${
              isReview
                ? 'border-[var(--border)] bg-[var(--surface-raised)] text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] focus:border-[var(--accent)]'
                : 'cursor-not-allowed border-transparent bg-transparent text-[var(--text-tertiary)] placeholder:text-[var(--text-tertiary)]'
            }`}
          />
          {error && <p className="mt-1 px-2 text-[11px] text-[var(--danger)]">{error}</p>}
        </div>

        <button
          onClick={sendRefinement}
          disabled={!isReview || !feedback.trim() || loading}
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-2xl bg-[var(--text-primary)] text-[var(--app-bg)] transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-35"
          aria-label="Send refinement"
        >
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
        </button>
      </div>
    </div>
  );
}
