'use client';
import { useParams, useRouter } from 'next/navigation';
import { useEffect, useRef, useState, useCallback } from 'react';
import { getRunStatus, RunNotFoundError } from '@/lib/api';
import { getRuns, updateRunStatus } from '@/lib/storage';
import { RunStatusResponse, MemoVersion } from '@/types';
import Sidebar from '@/components/Sidebar';
import DebateFeed from '@/components/DebateFeed';
import QueryBox from '@/components/QueryBox';
import ThemeToggle from '@/components/ThemeToggle';
import { useThemeMode } from '@/components/useThemeMode';

const POLL_MS = 2000;

const STATUS_LABEL: Record<string, string> = {
  running: 'Running',
  awaiting_review: 'Memo ready for refinement',
  completed: 'Completed',
  error: 'Error',
};

const STATUS_PULSE: Record<string, string> = {
  running: 'bg-[var(--cobalt)] animate-pulse',
  awaiting_review: 'bg-[var(--amber)] animate-pulse',
  completed: 'bg-[var(--emerald)]',
  error: 'bg-[var(--danger)]',
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
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const { theme, toggleTheme } = useThemeMode();

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
      if (data.problem_statement) setProblemStatement(data.problem_statement);

      // Only snapshot a memo when the graph has fully paused for review.
      // During re-processing (status=running), the backend still holds the
      // previous final_memo — capturing it then would show the old memo as v2.
      if (data.memo_versions?.length) {
        setMemoVersions(data.memo_versions);
      } else if (data.final_memo && data.status === 'awaiting_review') {
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
      <div data-theme={theme} className="executive-shell flex h-screen">
        <Sidebar />
        <div className="flex flex-1 flex-col items-center justify-center gap-3 text-[var(--text-primary)]">
          <p className="text-sm font-semibold">Run not found</p>
          <p className="max-w-xs text-center text-xs text-[var(--text-secondary)]">
            The backend was restarted and its in-memory store was cleared.
            This run no longer exists on the server.
          </p>
          <button
            onClick={() => router.push('/')}
            className="mt-2 text-xs font-semibold text-[var(--accent-strong)] underline"
          >
            Start a new debate
          </button>
        </div>
      </div>
    );
  }

  if (fetchError) {
    return (
      <div data-theme={theme} className="executive-shell flex h-screen">
        <Sidebar />
        <div className="flex flex-1 flex-col items-center justify-center gap-4">
          <p className="text-sm text-[var(--danger)]">Could not reach backend: {fetchError}</p>
          <button
            onClick={() => router.push('/')}
            className="text-xs font-semibold text-[var(--accent-strong)] underline"
          >
            Start a new debate
          </button>
        </div>
      </div>
    );
  }

  return (
    <div data-theme={theme} className="executive-shell flex h-screen overflow-hidden text-[var(--text-primary)]">
      <Sidebar collapsed={!sidebarOpen} onToggle={() => setSidebarOpen(open => !open)} />

      <div className="relative flex min-w-0 flex-1 flex-col overflow-hidden">
        <div className="flex shrink-0 items-center gap-3 border-b border-[var(--border)] bg-[var(--surface)]/75 px-6 py-4 backdrop-blur">
          <div
            className={`h-2.5 w-2.5 shrink-0 rounded-full ${
              STATUS_PULSE[statusData?.status ?? ''] ?? 'bg-slate-700'
            }`}
          />
          <span className="text-sm font-medium text-[var(--text-secondary)]">
            {STATUS_LABEL[statusData?.status ?? ''] ?? 'Loading…'}
            {statusData?.feedback_round
              ? ` · refinement ${statusData.feedback_round}`
              : ''}
          </span>
          {memoVersions.length > 0 && (
            <span className="ml-1 rounded-full border border-[var(--border)] px-2.5 py-1 text-xs font-semibold text-[var(--text-secondary)]">
              {memoVersions.length} memo version{memoVersions.length > 1 ? 's' : ''}
            </span>
          )}
          {statusData?.status === 'running' && (
            <span className="font-mono text-xs text-[var(--text-tertiary)]">
              {Math.floor(elapsed / 60)}:{String(elapsed % 60).padStart(2, '0')}
              {elapsed > 60 && (
                <span className="ml-1.5 font-sans">
                  · ~{Math.ceil((180 - elapsed) / 60)}min left
                </span>
              )}
            </span>
          )}
          <span className="ml-auto select-all font-mono text-[10px] text-[var(--text-tertiary)]">
            {runId.slice(0, 8)}…
          </span>
          <ThemeToggle theme={theme} onToggle={toggleTheme} />
        </div>

        <div className="relative flex-1 overflow-hidden px-4 py-6 sm:px-6">
          {statusData ? (
            <DebateFeed
              status={statusData}
              memoVersions={memoVersions}
              problemStatement={problemStatement}
            />
          ) : (
            <div className="flex h-32 items-center justify-center gap-2 text-sm text-[var(--text-secondary)]">
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-[var(--accent)] border-t-transparent" />
              Loading run…
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {(statusData?.status === 'running' || statusData?.status === 'awaiting_review') && (
          <div className="pointer-events-none absolute bottom-0 left-0 right-0 z-20 bg-gradient-to-t from-[var(--app-bg)] via-[var(--app-bg)]/80 to-transparent px-4 pb-4 pt-8 sm:px-8">
            <div className="pointer-events-auto mx-auto max-w-3xl">
              <QueryBox runId={runId} status={statusData.status} onAction={handleAction} />
            </div>
          </div>
        )}

        {statusData?.status === 'completed' && (
          <div className="shrink-0 border-t border-[var(--border)] px-6 pb-4 pt-2 text-center">
            <p className="text-xs text-[var(--text-tertiary)]">Debate complete</p>
          </div>
        )}

        {statusData?.status === 'error' && (
          <div className="shrink-0 border-t border-[var(--border)] px-6 pb-4 pt-2 text-center">
            <button
              onClick={() => window.location.href = '/'}
              className="text-xs font-semibold text-[var(--accent-strong)] underline"
            >
              Start a new debate
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
