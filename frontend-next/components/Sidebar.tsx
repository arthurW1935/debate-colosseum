'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { deleteRun, getRuns } from '@/lib/storage';
import { StoredRun } from '@/types';
import { MessageSquare, PanelLeftClose, PanelLeftOpen, Plus, Sparkles, Trash2 } from 'lucide-react';

const STATUS_DOT: Record<string, string> = {
  running: 'bg-[var(--cobalt)] animate-pulse',
  awaiting_review: 'bg-[var(--amber)] animate-pulse',
  completed: 'bg-[var(--emerald)]',
  error: 'bg-[var(--danger)]',
};

interface SidebarProps {
  collapsed?: boolean;
  onToggle?: () => void;
}

export default function Sidebar({ collapsed = false, onToggle }: SidebarProps) {
  const params = useParams();
  const router = useRouter();
  const activeRunId = params?.runId as string | undefined;
  const [runs, setRuns] = useState<StoredRun[]>([]);

  useEffect(() => {
    setRuns(getRuns());
    const id = setInterval(() => setRuns(getRuns()), 3000);
    return () => clearInterval(id);
  }, []);

  const removeRun = (runId: string) => {
    deleteRun(runId);
    setRuns(getRuns());
    if (activeRunId === runId) router.push('/');
  };

  if (collapsed) {
    return (
      <aside className="hidden h-screen w-20 shrink-0 border-r border-[var(--border)] bg-[var(--surface-subtle)]/80 p-3 md:flex md:flex-col md:items-center">
        <button
          type="button"
          onClick={onToggle}
          className="mt-3 flex h-11 w-11 items-center justify-center rounded-2xl border border-[var(--border)] bg-[var(--surface)] text-[var(--text-primary)] transition hover:-translate-y-0.5"
          aria-label="Show side panel"
        >
          <PanelLeftOpen className="h-4 w-4" />
        </button>
        <button
          type="button"
          onClick={() => router.push('/')}
          className="mt-8 flex h-10 w-10 items-center justify-center rounded-2xl border border-[var(--border)] bg-[var(--surface)] text-[var(--text-primary)] transition hover:-translate-y-0.5"
          aria-label="New debate"
        >
          <Plus className="h-4 w-4" />
        </button>
      </aside>
    );
  }

  return (
    <aside className="flex h-screen w-72 shrink-0 flex-col border-r border-[var(--border)] bg-[var(--surface-subtle)]/80">
      <div className="px-5 py-5">
        <div className="flex items-center justify-between gap-3">
          <div className="flex min-w-0 items-center gap-2">
            <span className="flex h-9 w-9 items-center justify-center rounded-2xl bg-[var(--text-primary)] text-xs font-bold text-[var(--app-bg)]">
              <Sparkles className="h-4 w-4" />
            </span>
            <span className="truncate text-sm font-semibold tracking-wide text-[var(--text-primary)]">
              Debate Colosseum
            </span>
          </div>
          {onToggle && (
            <button
              type="button"
              onClick={onToggle}
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-2xl border border-[var(--border)] bg-[var(--surface)] text-[var(--text-secondary)] transition hover:-translate-y-0.5 hover:text-[var(--text-primary)]"
              aria-label="Hide side panel"
            >
              <PanelLeftClose className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      <div className="p-3">
        <button
          onClick={() => router.push('/')}
          className="flex w-full items-center gap-2 rounded-2xl border border-[var(--border)] bg-[var(--surface)] px-4 py-3 text-sm font-semibold text-[var(--text-primary)] shadow-sm transition hover:-translate-y-0.5"
        >
          <Plus className="h-4 w-4" />
          New decision
        </button>
      </div>

      <div className="px-5 pb-2 pt-4 text-[10px] font-semibold uppercase tracking-[0.2em] text-[var(--text-tertiary)]">
        Recent decisions
      </div>

      <div className="flex-1 space-y-1 overflow-y-auto px-3 pb-4">
        {runs.length === 0 && (
          <p className="mt-6 px-4 text-center text-xs text-[var(--text-tertiary)]">No debates yet</p>
        )}
        {runs.map(run => (
          <div key={run.run_id} className="group relative">
            <Link
              href={`/run/${run.run_id}`}
              className={`flex items-start gap-3 rounded-2xl px-3 py-3 transition ${
                activeRunId === run.run_id
                  ? 'border border-[var(--border-strong)] bg-[var(--surface)] text-[var(--text-primary)] shadow-sm'
                  : 'text-[var(--text-secondary)] hover:bg-[var(--surface)]/70 hover:text-[var(--text-primary)]'
              }`}
            >
              <MessageSquare className="mt-0.5 h-4 w-4 shrink-0 opacity-55" />
              <div className="min-w-0 flex-1 pr-8">
                <p className="truncate text-xs font-medium leading-snug">
                  {run.problem_statement.length > 58
                    ? run.problem_statement.slice(0, 58) + '...'
                    : run.problem_statement}
                </p>
                <div className="mt-2 flex items-center gap-1.5">
                  <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${STATUS_DOT[run.status] ?? 'bg-[var(--text-tertiary)]'}`} />
                  <span className="text-[10px] capitalize text-[var(--text-tertiary)]">
                    {run.status.replace('_', ' ')}
                  </span>
                </div>
              </div>
            </Link>
            <button
              type="button"
              onClick={e => {
                e.preventDefault();
                e.stopPropagation();
                removeRun(run.run_id);
              }}
              className="absolute right-3 top-3 flex h-8 w-8 items-center justify-center rounded-xl border border-[var(--danger)]/20 bg-[var(--danger)]/10 text-[var(--danger)] opacity-0 transition hover:bg-[var(--danger)]/15 group-hover:opacity-100"
              aria-label="Delete decision"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          </div>
        ))}
      </div>
    </aside>
  );
}
