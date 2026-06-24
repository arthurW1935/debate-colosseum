import { StoredRun, RunStatus } from '@/types';

const KEY = 'debate_colosseum_runs';

export function getRuns(): StoredRun[] {
  if (typeof window === 'undefined') return [];
  try {
    return JSON.parse(localStorage.getItem(KEY) ?? '[]');
  } catch {
    return [];
  }
}

export function addRun(run: StoredRun): void {
  const runs = getRuns();
  const idx = runs.findIndex(r => r.run_id === run.run_id);
  if (idx >= 0) {
    runs[idx] = run;
  } else {
    runs.unshift(run);
  }
  localStorage.setItem(KEY, JSON.stringify(runs.slice(0, 50)));
}

export function updateRunStatus(runId: string, status: RunStatus): void {
  const runs = getRuns();
  const run = runs.find(r => r.run_id === runId);
  if (run) {
    run.status = status;
    localStorage.setItem(KEY, JSON.stringify(runs));
  }
}
