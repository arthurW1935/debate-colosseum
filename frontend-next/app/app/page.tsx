'use client';
import { useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { createRun } from '@/lib/api';
import { addRun } from '@/lib/storage';
import { getUserFromToken } from '@/lib/auth';
import AuthGuard from '@/components/AuthGuard';
import Sidebar from '@/components/Sidebar';
import ThemeToggle from '@/components/ThemeToggle';
import { useThemeMode } from '@/components/useThemeMode';
import { ArrowRight, FileText, Loader2, PanelLeftOpen, Plus, X } from 'lucide-react';

export default function AppPage() {
  const router = useRouter();
  const user = getUserFromToken();
  const firstName = user?.name?.split(' ')[0] || 'there';
  const [problem, setProblem] = useState('');
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { theme, toggleTheme } = useThemeMode();
  const fileRef = useRef<HTMLInputElement>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!problem.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const result = await createRun(problem.trim(), files);
      addRun({
        run_id: result.run_id,
        problem_statement: problem.trim(),
        created_at: new Date().toISOString(),
        status: 'running',
      });
      router.push(`/run/${result.run_id}`);
    } catch (e) {
      setError(String(e));
      setLoading(false);
    }
  };

  const addFiles = (incoming: FileList | null) => {
    if (!incoming) return;
    setFiles(prev => [...prev, ...Array.from(incoming)]);
  };

  return (
    <AuthGuard>
      <div
        data-theme={theme}
        className="executive-shell relative flex min-h-screen overflow-hidden text-[var(--text-primary)]"
        onDragOver={e => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={e => {
          e.preventDefault();
          setDragging(false);
          addFiles(e.dataTransfer.files);
        }}
      >
        {sidebarOpen && <Sidebar onToggle={() => setSidebarOpen(false)} />}

        {!sidebarOpen && (
          <button
            type="button"
            onClick={() => setSidebarOpen(true)}
            className="absolute left-6 top-6 z-30 flex h-11 w-11 items-center justify-center rounded-2xl border border-[var(--border)] bg-[var(--surface)] text-[var(--text-primary)] shadow-sm transition hover:-translate-y-0.5"
            aria-label="Show side panel"
          >
            <PanelLeftOpen className="h-4 w-4" />
          </button>
        )}

        <main className="relative flex min-h-screen flex-1 flex-col items-center justify-center px-4">
          <div className="absolute right-6 top-6 z-20">
            <ThemeToggle theme={theme} onToggle={toggleTheme} />
          </div>

          <div className="relative z-10 w-full max-w-3xl">
            <div className="mb-10 text-center">
              <p className="mb-4 text-xs font-semibold uppercase tracking-[0.28em] text-[var(--accent-strong)]">
                Debate Colosseum
              </p>
              <h1 className="font-serif-memo text-4xl leading-tight tracking-[-0.025em] text-[var(--text-primary)] sm:text-5xl">
                What's the next move, {firstName}?
              </h1>
              <p className="mx-auto mt-5 max-w-2xl text-base leading-7 text-[var(--text-secondary)]">
                A not-so-calm executive workspace where specialist agents debate growth, finance, and risk before drafting a serious decision memo.
              </p>
            </div>

            <form onSubmit={handleSubmit}>
              <div
                className={`glass-panel overflow-hidden rounded-[32px] transition ${
                  dragging ? 'scale-[1.01] border-[var(--accent)] ring-4 ring-[var(--accent-soft)]' : ''
                }`}
              >
                <textarea
                  value={problem}
                  onChange={e => setProblem(e.target.value)}
                  onKeyDown={e => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      if (problem.trim() && !loading) {
                        e.currentTarget.form?.requestSubmit();
                      }
                    }
                  }}
                  placeholder="Should we expand into the EU market next quarter? Include constraints, documents, or board context..."
                  rows={5}
                  className="w-full resize-none bg-transparent px-6 pb-3 pt-6 text-base leading-7 text-[var(--text-primary)] outline-none placeholder:text-[var(--text-tertiary)]"
                />

                <div className="border-t border-[var(--border)] bg-[var(--surface)]/50 px-5 py-4">
                  {files.length > 0 && (
                    <div className="mb-3 flex flex-wrap gap-2">
                      {files.map((f, i) => (
                        <span
                          key={i}
                          className="inline-flex items-center gap-2 rounded-full border border-[var(--border)] bg-[var(--surface-raised)] px-3 py-1.5 text-xs font-medium text-[var(--text-secondary)]"
                        >
                          <FileText className="h-3.5 w-3.5 text-[var(--accent-strong)]" />
                          {f.name}
                          <button
                            type="button"
                            onClick={() => setFiles(prev => prev.filter((_, idx) => idx !== i))}
                            className="rounded-full p-0.5 transition hover:bg-[var(--surface-subtle)]"
                            aria-label={`Remove ${f.name}`}
                          >
                            <X className="h-3 w-3" />
                          </button>
                        </span>
                      ))}
                    </div>
                  )}
                  <div className="flex items-center justify-between gap-3">
                    <button
                      type="button"
                      onClick={() => fileRef.current?.click()}
                      className="inline-flex items-center gap-2 rounded-full border border-[var(--border)] bg-[var(--surface-raised)] px-3.5 py-2 text-xs font-semibold text-[var(--text-secondary)] transition hover:-translate-y-0.5 hover:text-[var(--text-primary)]"
                    >
                      <Plus className="h-3.5 w-3.5" />
                      Add documents
                    </button>
                    <span className="hidden text-xs text-[var(--text-tertiary)] sm:inline">
                      Drag and drop PDF, TXT, or MD files anywhere
                    </span>
                    <button
                      type="submit"
                      disabled={!problem.trim() || loading}
                      className="inline-flex items-center gap-2 rounded-full bg-[var(--text-primary)] px-5 py-2.5 text-sm font-semibold text-[var(--app-bg)] transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-40"
                    >
                      {loading ? (
                        <>
                          <Loader2 className="h-4 w-4 animate-spin" />
                          Starting
                        </>
                      ) : (
                        <>
                          Start debate
                          <ArrowRight className="h-4 w-4" />
                        </>
                      )}
                    </button>
                  </div>
                  <input
                    ref={fileRef}
                    type="file"
                    accept=".pdf,.txt,.md"
                    multiple
                    className="hidden"
                    onChange={e => addFiles(e.target.files)}
                  />
                </div>
              </div>

              {error && (
                <div className="mt-3 rounded-2xl border border-[var(--danger)]/25 bg-[var(--danger)]/10 px-4 py-3">
                  <p className="text-xs text-[var(--danger)]">{error}</p>
                </div>
              )}
            </form>

            <div className="mx-auto mt-10 grid max-w-2xl grid-cols-1 gap-3 text-sm sm:grid-cols-3">
              {[
                ['Market expansion', 'Stress-test demand, timing, and rollout risk.'],
                ['Pricing change', 'Debate growth upside against margin pressure.'],
                ['Hiring plan', 'Evaluate runway, delivery risk, and sequencing.'],
              ].map(([title, body]) => (
                <button
                  key={title}
                  type="button"
                  onClick={() => setProblem(body)}
                  className="rounded-3xl border border-[var(--border)] bg-[var(--surface)]/65 p-4 text-left shadow-sm transition hover:-translate-y-1 hover:border-[var(--border-strong)]"
                >
                  <p className="font-semibold text-[var(--text-primary)]">{title}</p>
                  <p className="mt-2 text-xs leading-5 text-[var(--text-secondary)]">{body}</p>
                </button>
              ))}
            </div>
          </div>
        </main>
      </div>
    </AuthGuard>
  );
}
