import { StoredRun } from '@/types';
import { getAuthHeaders } from './auth';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8000';

export async function fetchUserRuns(): Promise<StoredRun[]> {
  const res = await fetch(`${API_BASE}/runs`, { headers: { ...getAuthHeaders() } });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  const data = await res.json();
  return data.runs.map((r: any) => ({
    run_id: r.id,
    problem_statement: r.problem_statement,
    status: r.status,
    created_at: r.created_at,
  }));
}
