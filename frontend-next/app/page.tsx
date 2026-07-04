'use client';
import { useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { createRun } from '@/lib/api';
import { addRun } from '@/lib/storage';
import { Upload, X, ArrowRight, Loader2 } from 'lucide-react';

export default function LandingPage() {
  const router = useRouter();
  const [problem, setProblem] = useState('');
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
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
    <div className="min-h-screen bg-[#0a0a0f] flex flex-col items-center justify-center px-4 relative overflow-hidden">
      {/* Ambient glow */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-indigo-900/20 rounded-full blur-[120px]" />
      </div>

      <div className="relative w-full max-w-xl z-10">
        {/* Hero */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-indigo-600/20 border border-indigo-500/30 mb-5 text-3xl">
            ⚔️
          </div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Debate Colosseum</h1>
          <p className="text-slate-500 mt-2 text-sm">
            Growth · Finance · Risk agents deliberate your hardest decisions
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          {/* Input card */}
          <div className="rounded-2xl bg-white/[0.04] border border-white/[0.08] overflow-hidden focus-within:border-indigo-500/40 transition-colors duration-200">
            <textarea
              value={problem}
              onChange={e => setProblem(e.target.value)}
              placeholder={`Describe the decision you need to make…\n\ne.g. Should we expand into the EU market next quarter? We have €2M ARR, 3 engineers, and no EU legal entity.`}
              rows={6}
              className="w-full bg-transparent px-5 pt-4 pb-3 text-sm text-slate-200 placeholder:text-slate-600 outline-none resize-none leading-relaxed"
            />

            {/* Attachment bar */}
            <div className="px-4 py-3 border-t border-white/[0.05] bg-white/[0.01]">
              {files.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-2.5">
                  {files.map((f, i) => (
                    <span
                      key={i}
                      className="flex items-center gap-1.5 text-xs bg-white/[0.07] text-slate-300 border border-white/[0.08] px-2.5 py-1 rounded-full"
                    >
                      📎 {f.name}
                      <button
                        type="button"
                        onClick={() => setFiles(prev => prev.filter((_, idx) => idx !== i))}
                        className="ml-0.5"
                      >
                        <X className="w-3 h-3 text-slate-500 hover:text-slate-300 transition-colors" />
                      </button>
                    </span>
                  ))}
                </div>
              )}
              <div className="flex items-center justify-between">
                <button
                  type="button"
                  onClick={() => fileRef.current?.click()}
                  className="flex items-center gap-1.5 text-xs text-slate-600 hover:text-slate-400 transition-colors"
                >
                  <Upload className="w-3.5 h-3.5" />
                  Attach documents
                </button>
                <span className="text-[10px] text-slate-700">PDF · TXT · MD</span>
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
            <div className="mt-3 px-4 py-2.5 rounded-xl bg-red-500/10 border border-red-500/20">
              <p className="text-xs text-red-400">{error}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={!problem.trim() || loading}
            className="w-full mt-3 flex items-center justify-center gap-2 py-3.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 disabled:bg-slate-800 disabled:text-slate-600 disabled:cursor-not-allowed text-sm font-semibold text-white transition-colors duration-150"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Starting debate…
              </>
            ) : (
              <>
                Start Debate
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
