'use client';
import { useParams, useRouter } from 'next/navigation';
import { useEffect, useRef, useState, useCallback } from 'react';
import { getRunStatus, RunNotFoundError } from '@/lib/api';
import { getRuns, updateRunStatus } from '@/lib/storage';
import { RunStatusResponse, MemoVersion } from '@/types';
import Sidebar from '@/components/Sidebar';
import DebateFeed from '@/components/DebateFeed';
import QueryBox from '@/components/QueryBox';

const POLL_MS = 2000;

const STATUS_LABEL: Record<string, string> = {
  running: 'Running',
  awaiting_review: 'Awaiting Review',
  completed: 'Completed',
  error: 'Error',
};

const STATUS_PULSE: Record<string, string> = {
  running: 'bg-blue-400 animate-pulse',
  awaiting_review: 'bg-amber-400 animate-pulse',
  completed: 'bg-emerald-500',
  error: 'bg-red-500',
};

export default function RunPage() {
  const params = useParams();
  const runId = params.runId as string;
  const router = useRouter();

  const [statusData, setStatusData] = useState<RunStatusResponse | null>(null);
  const [memoVersions, setMemoVersions] = useState<MemoVersion[]>([]);
  const [problemStatement, setProblemStatement] = useState('');
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [elapsed, setElapsed] = useState(0);

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const runs = getRuns();
    const run = runs.find(r => r.run_id === runId);
    if (run) setProblemStatement(run.problem_statement);
  }, [runId]);

  const poll = useCallback(async () => {
    try {
      const data: RunStatusResponse = await getRunStatus(runId);
      setStatusData(data);

      // Only snapshot a memo when the graph has fully paused for review.
      // During re-processing (status=running), the backend still holds the
      // previous final_memo — capturing it then would show the old memo as v2.
      if (data.final_memo && data.status === 'awaiting_review') {
        const version = data.feedback_round + 1;
        setMemoVersions(prev => {
          const alreadyHas = prev.some(mv => mv.version === version);
          if (alreadyHas) return prev;
          return [...prev, { memo: data.final_memo!, version }];
        });
      }

      updateRunStatus(runId, data.status);
    } catch (e) {
      if (e instanceof RunNotFoundError) {
        // Server restarted — stop polling, mark run expired in sidebar
        if (pollRef.current) clearInterval(pollRef.current);
        if (timerRef.current) clearInterval(timerRef.current);
        updateRunStatus(runId, 'error');
        setNotFound(true);
      } else {
        setFetchError(String(e));
      }
    }
  }, [runId]);

  useEffect(() => {
    poll();
    pollRef.current = setInterval(poll, POLL_MS);
    // Elapsed timer — ticks every second while running
    timerRef.current = setInterval(() => setElapsed(s => s + 1), 1000);
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [poll]);

  // Stop polling + timer once terminal
  useEffect(() => {
    if (statusData?.status === 'completed' || statusData?.status === 'error') {
      if (pollRef.current) clearInterval(pollRef.current);
      if (timerRef.current) clearInterval(timerRef.current);
    }
    // Reset timer when re-processing after feedback
    if (statusData?.status === 'running' && !timerRef.current) {
      timerRef.current = setInterval(() => setElapsed(s => s + 1), 1000);
    }
  }, [statusData?.status]);

  // Auto-scroll to bottom when new content arrives
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [memoVersions.length, statusData?.status]);

  const handleAction = useCallback(
    (decision: 'approved' | 'feedback' | 'abandoned', feedbackText?: string) => {
      if (decision === 'feedback' && feedbackText) {
        // Attach feedback text to the current latest memo for display
        setMemoVersions(prev => {
          if (!prev.length) return prev;
          return prev.map((mv, i) =>
            i === prev.length - 1 ? { ...mv, feedbackText } : mv
          );
        });
        // Resume polling for the new revision
        if (pollRef.current) clearInterval(pollRef.current);
        pollRef.current = setInterval(poll, POLL_MS);
      }
      if (decision === 'approved' || decision === 'abandoned') {
        // Resume poll briefly to pick up completed state
        if (pollRef.current) clearInterval(pollRef.current);
        pollRef.current = setInterval(poll, POLL_MS);
      }
    },
    [poll]
  );

  if (notFound) {
    return (
      <div className="flex h-screen bg-[#0a0a0f]">
        <Sidebar />
        <div className="flex-1 flex flex-col items-center justify-center gap-3">
          <p className="text-2xl">⚠️</p>
          <p className="text-sm text-slate-300 font-medium">Run not found</p>
          <p className="text-xs text-slate-500 text-center max-w-xs">
            The backend was restarted and its in-memory store was cleared.
            This run no longer exists on the server.
          </p>
          <button
            onClick={() => router.push('/')}
            className="mt-2 text-xs text-indigo-400 hover:text-indigo-300 underline"
          >
            ← Start a new debate
          </button>
        </div>
      </div>
    );
  }

  if (fetchError) {
    return (
      <div className="flex h-screen bg-[#0a0a0f]">
        <Sidebar />
        <div className="flex-1 flex flex-col items-center justify-center gap-4">
          <p className="text-sm text-red-400">Could not reach backend: {fetchError}</p>
          <button
            onClick={() => router.push('/')}
            className="text-xs text-indigo-400 hover:text-indigo-300 underline"
          >
            ← Start a new debate
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-[#0a0a0f] text-white overflow-hidden">
      <Sidebar />

      <div className="flex-1 flex flex-col overflow-hidden min-w-0">
        {/* Top bar */}
        <div className="px-6 py-3 border-b border-white/[0.05] flex items-center gap-3 shrink-0 bg-[#0d0d14]">
          <div
            className={`w-2 h-2 rounded-full shrink-0 ${
              STATUS_PULSE[statusData?.status ?? ''] ?? 'bg-slate-700'
            }`}
          />
          <span className="text-xs text-slate-400">
            {STATUS_LABEL[statusData?.status ?? ''] ?? 'Loading…'}
            {statusData?.feedback_round
              ? ` · feedback round ${statusData.feedback_round}`
              : ''}
          </span>
          {memoVersions.length > 0 && (
            <span className="text-xs text-slate-600 ml-1">
              · {memoVersions.length} version{memoVersions.length > 1 ? 's' : ''}
            </span>
          )}
          {statusData?.status === 'running' && (
            <span className="text-xs text-slate-500 font-mono">
              {Math.floor(elapsed / 60)}:{String(elapsed % 60).padStart(2, '0')}
              {elapsed > 60 && (
                <span className="text-slate-600 ml-1.5 font-sans">
                  · ~{Math.ceil((180 - elapsed) / 60)}min left
                </span>
              )}
            </span>
          )}
          <span className="ml-auto font-mono text-[10px] text-slate-700 select-all">
            {runId.slice(0, 8)}…
          </span>
        </div>

        {/* Scrollable feed */}
        <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-5">
          {statusData ? (
            <DebateFeed
              status={statusData}
              memoVersions={memoVersions}
              problemStatement={problemStatement}
            />
          ) : (
            <div className="flex items-center justify-center h-32 gap-2 text-slate-500 text-sm">
              <div className="w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
              Loading run…
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Query box / HITL */}
        {statusData && statusData.status === 'running' && (
          <div className="px-4 sm:px-6 pb-4 pt-2 shrink-0 border-t border-white/[0.04] bg-[#0d0d14]">
            <QueryBox runId={runId} status={statusData.status} onAction={handleAction} />
          </div>
        )}

        {statusData?.status === 'awaiting_review' && (
          <div className="px-4 sm:px-6 pb-4 pt-2 shrink-0 border-t border-white/[0.04] bg-[#0d0d14]">
            <QueryBox runId={runId} status={statusData.status} onAction={handleAction} />
          </div>
        )}

        {statusData?.status === 'completed' && (
          <div className="px-6 pb-4 pt-2 shrink-0 border-t border-white/[0.04] text-center">
            <p className="text-xs text-slate-700">Debate complete</p>
          </div>
        )}

        {statusData?.status === 'error' && (
          <div className="px-6 pb-4 pt-2 shrink-0 border-t border-white/[0.04] text-center">
            <button
              onClick={() => window.location.href = '/'}
              className="text-xs text-indigo-400 hover:text-indigo-300 underline"
            >
              ← Start a new debate
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
