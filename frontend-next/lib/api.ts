import { RunStatusResponse } from '@/types';
import { getAuthHeaders } from './auth';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8000';

export async function createRun(
  problemStatement: string,
  files: File[]
): Promise<{ run_id: string; status: string }> {
  const formData = new FormData();
  formData.append('problem_statement', problemStatement);
  for (const file of files) {
    formData.append('files', file);
  }
  const res = await fetch(`${API_BASE}/runs`, { 
    method: 'POST', 
    body: formData,
    headers: { ...getAuthHeaders() }
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  return res.json();
}

export class RunNotFoundError extends Error {
  constructor(runId: string) {
    super(`Run ${runId} not found — the backend was likely restarted (in-memory store cleared).`);
    this.name = 'RunNotFoundError';
  }
}

export async function getRunStatus(runId: string): Promise<RunStatusResponse> {
  const res = await fetch(`${API_BASE}/runs/${runId}/status`, {
    headers: { ...getAuthHeaders() }
  });
  if (res.status === 404) throw new RunNotFoundError(runId);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function submitReview(
  runId: string,
  decision: 'approved' | 'feedback' | 'abandoned',
  feedbackText?: string
): Promise<{ run_id: string; status: string; message: string }> {
  const res = await fetch(`${API_BASE}/runs/${runId}/review`, {
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json',
      ...getAuthHeaders()
    },
    body: JSON.stringify({ decision, feedback_text: feedbackText }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  return res.json();
}
