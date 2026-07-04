'use client';
import { useEffect, useMemo, useState } from 'react';
import { RunStatusResponse, MemoVersion } from '@/types';
import MemoCard from './MemoCard';
import { Loader2, PanelLeftClose, PanelLeftOpen } from 'lucide-react';

interface DebateFeedProps {
  status: RunStatusResponse;
  memoVersions: MemoVersion[];
  problemStatement: string;
}

const AGENTS = [
  { label: 'Growth', sub: 'market perspective', x: 150, y: 118, color: 'var(--cobalt)', delay: '' },
  { label: 'Finance', sub: 'capital perspective', x: 150, y: 300, color: 'var(--emerald)', delay: 'agent-float-delay' },
  { label: 'Risk', sub: 'downside perspective', x: 510, y: 118, color: 'var(--danger)', delay: 'agent-float-delay' },
  { label: 'Arbiter', sub: 'dispute handler', x: 510, y: 300, color: '#b78cff', delay: '' },
  { label: 'Synthesizer', sub: 'memo drafter', x: 330, y: 390, color: 'var(--accent)', delay: 'agent-float-delay' },
];

const TYPING_LINES = [
  'Specialists are debating from their strongest perspectives.',
  'They are the best in their own specific fields.',
  'Please stay calm while they shout at each other.',
];

function AgentNode({ agent }: { agent: (typeof AGENTS)[number] }) {
  return (
    <g className={`agent-float ${agent.delay}`} style={{ transformOrigin: `${agent.x}px ${agent.y}px` }}>
      <circle cx={agent.x} cy={agent.y} r="46" fill={agent.color} opacity="0.14" />
      <circle cx={agent.x} cy={agent.y} r="34" fill="var(--surface)" stroke="var(--border)" />
      <circle cx={agent.x} cy={agent.y - 12} r="10" fill={agent.color} />
      <text x={agent.x} y={agent.y + 60} textAnchor="middle" fill="var(--text-primary)" fontSize="14" fontWeight="650">
        {agent.label}
      </text>
      <text x={agent.x} y={agent.y + 80} textAnchor="middle" fill="var(--text-tertiary)" fontSize="11">
        {agent.sub}
      </text>
    </g>
  );
}

function AgentOrchestration({ revision }: { revision?: number }) {
  const [lineIndex, setLineIndex] = useState(0);
  const [displayedText, setDisplayedText] = useState('');
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    const current = TYPING_LINES[lineIndex];
    const delay = !deleting && displayedText === current ? 1300 : deleting && displayedText === '' ? 300 : 34;

    const timer = setTimeout(() => {
      if (!deleting && displayedText.length < current.length) {
        setDisplayedText(current.slice(0, displayedText.length + 1));
        return;
      }

      if (!deleting && displayedText === current) {
        setDeleting(true);
        return;
      }

      if (deleting && displayedText.length > 0) {
        setDisplayedText(current.slice(0, displayedText.length - 1));
        return;
      }

      setDeleting(false);
      setLineIndex(index => (index + 1) % TYPING_LINES.length);
    }, delay);

    return () => clearTimeout(timer);
  }, [deleting, displayedText, lineIndex]);

  return (
    <div className="relative flex min-h-[calc(100vh-96px)] overflow-hidden">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-1/2 top-[40%] h-[540px] w-[720px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[var(--cobalt)]/10 blur-[110px]" />
        <div className="absolute bottom-0 right-0 h-[360px] w-[420px] rounded-full bg-[var(--accent)]/10 blur-[100px]" />
      </div>

      <div className="relative z-10 flex w-full flex-col p-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[var(--accent)]">
            Live debate
          </p>
          <h2 className="mt-2 text-2xl font-semibold text-[var(--text-primary)]">
            Specialists are debating
          </h2>
        </div>
        <div className="flex items-center gap-2 rounded-full border border-[var(--border)] bg-[var(--surface)]/70 px-3 py-2 text-xs text-[var(--text-secondary)] shadow-sm">
          <Loader2 className="h-3.5 w-3.5 animate-spin text-[var(--accent)]" />
          {revision ? `Refinement v${revision} in progress` : 'Working live'}
        </div>
      </div>

      <div className="relative mx-auto flex min-h-0 flex-1 items-center justify-center pb-20">
        <div className="h-[min(56vh,500px)] w-full max-w-4xl">
        <svg viewBox="0 0 660 500" className="h-full w-full">
          <defs>
            <filter id="glow">
              <feGaussianBlur stdDeviation="6" result="coloredBlur" />
              <feMerge>
                <feMergeNode in="coloredBlur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
          {AGENTS.map(agent => (
            <line
              key={`line-${agent.label}`}
              x1="330"
              y1="235"
              x2={agent.x}
              y2={agent.y}
              stroke="var(--border-strong)"
              opacity="0.62"
              strokeWidth="2"
              className="agent-edge"
            />
          ))}
          <circle cx="330" cy="235" r="74" fill="var(--accent)" opacity="0.12" filter="url(#glow)" />
          <foreignObject x="264" y="169" width="132" height="132">
            <div className="moderator-pulse flex h-full w-full flex-col items-center justify-center rounded-full border border-[var(--border-strong)] bg-[var(--surface)] text-center shadow-[var(--shadow-card)]">
              <span className="text-sm font-semibold text-[var(--text-primary)]">Moderator</span>
              <span className="mt-1 text-[11px] text-[var(--text-tertiary)]">managing the debate</span>
            </div>
          </foreignObject>
          {AGENTS.map(agent => <AgentNode key={agent.label} agent={agent} />)}
        </svg>
        </div>
      </div>

      <div className="absolute bottom-36 left-1/2 min-h-[28px] w-[min(90vw,42rem)] -translate-x-1/2 text-center">
        <p className="text-sm font-medium leading-7 text-[var(--text-secondary)]">
          {displayedText}
          <span className="ml-0.5 inline-block h-4 w-px translate-y-0.5 animate-pulse bg-[var(--accent)]" />
        </p>
      </div>
      </div>
    </div>
  );
}

export default function DebateFeed({ status, memoVersions, problemStatement }: DebateFeedProps) {
  const { status: s, feedback_round } = status;
  const [selectedVersion, setSelectedVersion] = useState<number | null>(null);
  const [queryTrailOpen, setQueryTrailOpen] = useState(false);

  const hasMemo = memoVersions.length > 0;
  const isReprocessing = s === 'running' && feedback_round > 0 && memoVersions.length <= feedback_round;
  const latestVersion = memoVersions[memoVersions.length - 1]?.version ?? null;

  useEffect(() => {
    if (latestVersion && selectedVersion === null) setSelectedVersion(latestVersion);
    if (latestVersion && selectedVersion && selectedVersion > latestVersion) setSelectedVersion(latestVersion);
  }, [latestVersion, selectedVersion]);

  const selectedMemo = useMemo(() => {
    if (!memoVersions.length) return null;
    return memoVersions.find(mv => mv.version === selectedVersion) ?? memoVersions[memoVersions.length - 1];
  }, [memoVersions, selectedVersion]);

  const queryTrail = useMemo(() => {
    const trail = [{ label: 'Initial brief', text: problemStatement || 'Decision brief unavailable' }];
    memoVersions.forEach(mv => {
      if (mv.feedbackText) {
        trail.push({ label: `Refinement ${mv.version}`, text: mv.feedbackText });
      }
    });
    return trail;
  }, [memoVersions, problemStatement]);

  if (s === 'running' && (!hasMemo || isReprocessing)) {
    return (
      <div className="-mx-4 -my-6 sm:-mx-6">
        <AgentOrchestration revision={isReprocessing ? feedback_round + 1 : undefined} />
      </div>
    );
  }

  return (
    <div className="mx-auto flex h-full w-full max-w-[86rem] flex-col pb-24">
      {selectedMemo && (
        <>
          <div className="mb-3 flex shrink-0 items-center justify-between gap-3">
            <button
              type="button"
              onClick={() => setQueryTrailOpen(open => !open)}
              className="inline-flex items-center gap-2 rounded-full border border-[var(--border)] bg-[var(--surface)]/80 px-3 py-1.5 text-xs font-semibold text-[var(--text-secondary)] shadow-sm transition hover:-translate-y-0.5 hover:text-[var(--text-primary)]"
            >
              {queryTrailOpen ? <PanelLeftClose className="h-3.5 w-3.5" /> : <PanelLeftOpen className="h-3.5 w-3.5" />}
              {queryTrailOpen ? 'Hide query trail' : 'Show query trail'}
            </button>

            {memoVersions.length > 0 && (
              <select
                value={selectedMemo.version}
                onChange={e => setSelectedVersion(Number(e.target.value))}
                className="memo-version-select rounded-full border border-[var(--border)] bg-[var(--surface)] px-3 py-1.5 text-xs font-semibold text-[var(--text-primary)] outline-none"
              >
                {memoVersions.map(mv => (
                  <option key={mv.version} value={mv.version}>
                    Version {mv.version}{mv.version === latestVersion ? ' (latest)' : ''}
                  </option>
                ))}
              </select>
            )}
          </div>

          <div
            className={
              queryTrailOpen
                ? 'grid min-h-0 flex-1 grid-cols-1 gap-4 xl:grid-cols-[250px_minmax(0,1fr)]'
                : 'mx-auto min-h-0 w-full max-w-[1120px] flex-1'
            }
          >
            {queryTrailOpen && (
              <aside className="glass-panel flex min-h-0 flex-col rounded-[28px] p-5">
                <p className="text-sm font-semibold text-[var(--text-primary)]">Query trail</p>
                <div className="mt-5 min-h-0 flex-1 space-y-5 overflow-y-auto pr-1">
                  {queryTrail.map((item, idx) => (
                    <div key={`${item.label}-${idx}`} className="relative pl-6">
                      {idx < queryTrail.length - 1 && (
                        <span className="absolute left-[5px] top-5 h-[calc(100%+20px)] w-px bg-[var(--border)]" />
                      )}
                      <span className={`absolute left-0 top-1 h-2.5 w-2.5 rounded-full ${idx === queryTrail.length - 1 ? 'bg-[var(--accent)]' : 'bg-[var(--border-strong)]'}`} />
                      <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--accent-strong)]">
                        {item.label}
                      </p>
                      <p className="mt-1 text-xs leading-5 text-[var(--text-secondary)]">{item.text}</p>
                    </div>
                  ))}
                </div>
              </aside>
            )}

            <MemoCard
              memo={selectedMemo.memo}
              version={selectedMemo.version}
              isLatest={selectedMemo.version === latestVersion}
            />
          </div>
        </>
      )}

      {!selectedMemo && s !== 'running' && (
        <div className="glass-panel rounded-[28px] p-8 text-center text-sm text-[var(--text-secondary)]">
          The memo is not ready yet. The specialists will return with a decision memo once the debate finishes.
        </div>
      )}

      {s === 'error' && status.error && (
        <div className="mt-6 rounded-3xl border border-[var(--danger)]/25 bg-[var(--danger)]/10 p-4">
          <p className="text-sm text-[var(--danger)]">
            <span className="font-semibold">Error: </span>
            {status.error}
          </p>
        </div>
      )}
    </div>
  );
}
