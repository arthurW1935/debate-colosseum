'use client';
import { useState } from 'react';
import { Send, CheckCircle2, Trash2, Loader2, MessageSquarePlus } from 'lucide-react';
import { submitReview } from '@/lib/api';
import { RunStatus } from '@/types';

interface QueryBoxProps {
  runId: string;
  status: RunStatus;
  onAction: (decision: 'approved' | 'feedback' | 'abandoned', feedbackText?: string) => void;
}

export default function QueryBox({ runId, status, onAction }: QueryBoxProps) {
  const [feedback, setFeedback] = useState('');
  const [showInput, setShowInput] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isReview = status === 'awaiting_review';
  const isRunning = status === 'running';

  const act = async (decision: 'approved' | 'feedback' | 'abandoned') => {
    if (decision === 'feedback' && !feedback.trim()) return;
    setLoading(true);
    setError(null);
    try {
      await submitReview(runId, decision, decision === 'feedback' ? feedback.trim() : undefined);
      onAction(decision, decision === 'feedback' ? feedback.trim() : undefined);
      if (decision === 'feedback') {
        setFeedback('');
        setShowInput(false);
      }
    } catch (e) {
      setError(String(e));
    }
    setLoading(false);
  };

  return (
    <div className={`rounded-2xl border transition-all duration-200 overflow-hidden ${
      isReview
        ? 'border-indigo-500/30 bg-[#15152a]'
        : 'border-white/[0.05] bg-white/[0.02]'
    }`}>
      {isReview && (
        <div className="px-4 pt-3 pb-2.5 border-b border-white/[0.06]">
          <p className="text-[11px] text-slate-500 mb-2">Review the memo above and choose an action:</p>
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => act('approved')}
              disabled={loading}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
              Approve &amp; Send
            </button>
            <button
              onClick={() => setShowInput(s => !s)}
              disabled={loading}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-colors disabled:opacity-50 ${
                showInput
                  ? 'bg-amber-600 text-white hover:bg-amber-500'
                  : 'bg-amber-600/20 text-amber-400 border border-amber-500/30 hover:bg-amber-600/30'
              }`}
            >
              <MessageSquarePlus className="w-3.5 h-3.5" />
              Send Feedback
            </button>
            <button
              onClick={() => act('abandoned')}
              disabled={loading}
              className="ml-auto flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-red-950/60 text-red-400 border border-red-900/40 hover:bg-red-900/40 text-xs font-semibold transition-colors disabled:opacity-50"
            >
              <Trash2 className="w-3.5 h-3.5" />
              Abandon
            </button>
          </div>
        </div>
      )}

      <div className="flex items-end gap-2 p-3">
        <div className="flex-1">
          <textarea
            value={isReview && showInput ? feedback : ''}
            onChange={e => setFeedback(e.target.value)}
            disabled={!isReview || !showInput || loading}
            rows={isReview && showInput ? 3 : 1}
            placeholder={
              isRunning
                ? '⏳  Agents are deliberating…'
                : isReview && showInput
                ? 'Enter feedback for the agents… (Shift+Enter for newline)'
                : isReview
                ? 'Click "Send Feedback" above to provide additional context…'
                : 'Debate complete'
            }
            onKeyDown={e => {
              if (e.key === 'Enter' && !e.shiftKey && isReview && showInput) {
                e.preventDefault();
                act('feedback');
              }
            }}
            className={`w-full resize-none rounded-xl px-3.5 py-2.5 text-sm outline-none transition-all leading-relaxed ${
              isReview && showInput
                ? 'bg-white/[0.06] border border-indigo-500/30 text-slate-200 placeholder:text-slate-600 focus:border-indigo-400/50'
                : 'bg-transparent border border-transparent text-slate-600 placeholder:text-slate-700 cursor-not-allowed'
            }`}
          />
          {error && <p className="text-[11px] text-red-400 mt-1 px-1">{error}</p>}
        </div>

        {isReview && showInput && (
          <button
            onClick={() => act('feedback')}
            disabled={!feedback.trim() || loading}
            className="shrink-0 w-9 h-9 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:cursor-not-allowed flex items-center justify-center transition-colors mb-0.5"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 text-white animate-spin" />
            ) : (
              <Send className="w-4 h-4 text-white" />
            )}
          </button>
        )}
      </div>
    </div>
  );
}
