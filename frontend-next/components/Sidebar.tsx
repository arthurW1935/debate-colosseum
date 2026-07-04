'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { getRuns } from '@/lib/storage';
import { fetchUserRuns } from '@/lib/runs-api';
import { StoredRun } from '@/types';
import { Plus, MessageSquare } from 'lucide-react';

const STATUS_DOT: Record<string, string> = {
  running: 'bg-blue-400 animate-pulse',
  awaiting_review: 'bg-amber-400 animate-pulse',
  completed: 'bg-green-500',
  error: 'bg-red-500',
};

export default function Sidebar() {
  const params = useParams();
  const router = useRouter();
  const activeRunId = params?.runId as string | undefined;
  const [runs, setRuns] = useState<StoredRun[]>([]);

  useEffect(() => {
    const loadRuns = async () => {
      try {
        const apiRuns = await fetchUserRuns();
        setRuns(apiRuns);
      } catch (e) {
        console.warn('API fetch failed, falling back to localStorage', e);
        setRuns(getRuns());
      }
    };
    loadRuns();
    const id = setInterval(loadRuns, 5000);
    return () => clearInterval(id);
  }, []);

  return (
    <aside className="w-60 shrink-0 flex flex-col bg-[#111118] border-r border-white/[0.05] h-screen">
      <div className="px-4 py-4 border-b border-white/[0.05]">
        <div className="flex items-center gap-2">
          <span className="text-lg">⚔️</span>
          <span className="text-sm font-semibold text-white tracking-wide">Debate Colosseum</span>
        </div>
      </div>

      <div className="p-2.5">
        <button
          onClick={() => router.push('/')}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-slate-400 hover:text-slate-200 hover:bg-white/[0.05] transition-colors"
        >
          <Plus className="w-4 h-4" />
          New Debate
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-2 pb-4 space-y-0.5">
        {runs.length === 0 && (
          <p className="text-xs text-slate-600 text-center px-4 mt-6">No debates yet</p>
        )}
        {runs.map(run => (
          <Link
            key={run.run_id}
            href={`/run/${run.run_id}`}
            className={`flex items-start gap-2.5 px-3 py-2.5 rounded-lg transition-colors group ${
              activeRunId === run.run_id
                ? 'bg-indigo-600/20 text-white'
                : 'text-slate-400 hover:bg-white/[0.04] hover:text-slate-200'
            }`}
          >
            <MessageSquare className="w-3.5 h-3.5 mt-0.5 shrink-0 opacity-50" />
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium truncate leading-snug">
                {run.problem_statement.length > 55
                  ? run.problem_statement.slice(0, 55) + '…'
                  : run.problem_statement}
              </p>
              <div className="flex items-center gap-1.5 mt-1">
                <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${STATUS_DOT[run.status] ?? 'bg-slate-600'}`} />
                <span className="text-[10px] text-slate-600 capitalize">
                  {run.status.replace('_', ' ')}
                </span>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </aside>
  );
}
