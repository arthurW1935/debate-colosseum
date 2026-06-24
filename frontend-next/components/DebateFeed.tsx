'use client';
import { RunStatusResponse, MemoVersion } from '@/types';
import MemoCard from './MemoCard';
import { CheckCircle2, Circle, Loader2 } from 'lucide-react';

const AGENT_ICON: Record<string, string> = { growth: '📈', finance: '💰', risk: '⚠️' };

function PhaseRow({
  icon,
  label,
  done,
  active,
}: {
  icon: string;
  label: string;
  done: boolean;
  active?: boolean;
}) {
  return (
    <div className={`flex items-center gap-2.5 ${!done && !active ? 'opacity-35' : ''}`}>
      {done ? (
        <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
      ) : active ? (
        <Loader2 className="w-4 h-4 text-indigo-400 animate-spin shrink-0" />
      ) : (
        <Circle className="w-4 h-4 text-slate-700 shrink-0" />
      )}
      <span className={`text-sm ${done ? 'text-slate-300' : active ? 'text-indigo-300' : 'text-slate-600'}`}>
        <span className="mr-1.5">{icon}</span>
        {label}
      </span>
    </div>
  );
}

function TurnBlock({
  turn,
  done,
  active,
  expertSummaries,
}: {
  turn: number;
  done: boolean;
  active: boolean;
  expertSummaries?: { role: string; rec: string; conf: number }[];
}) {
  return (
    <div className={!done && !active ? 'opacity-35' : ''}>
      <div className="flex items-center gap-2.5 mb-2">
        <div
          className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0 ${
            done
              ? 'bg-emerald-500 text-black'
              : active
              ? 'bg-indigo-500 text-white'
              : 'bg-slate-800 text-slate-500'
          }`}
        >
          {turn}
        </div>
        <span
          className={`text-sm font-medium ${
            done ? 'text-slate-300' : active ? 'text-indigo-300' : 'text-slate-600'
          }`}
        >
          Turn {turn} — Expert Analysis
        </span>
        {active && <Loader2 className="w-3.5 h-3.5 text-indigo-400 animate-spin" />}
        {done && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />}
      </div>

      <div className="ml-7 space-y-1.5 mb-1">
        {(['growth', 'finance', 'risk'] as const).map(role => {
          const pos = expertSummaries?.find(p => p.role === role);
          return (
            <div key={role} className="flex items-center gap-2">
              {done ? (
                <CheckCircle2 className="w-3 h-3 text-emerald-500 shrink-0" />
              ) : active ? (
                <Loader2 className="w-3 h-3 text-indigo-400 animate-spin shrink-0" />
              ) : (
                <Circle className="w-3 h-3 text-slate-700 shrink-0" />
              )}
              <span className={`text-xs ${done || active ? 'text-slate-400' : 'text-slate-700'}`}>
                {AGENT_ICON[role]}{' '}
                <span className="capitalize">{role}</span> Agent
                {pos && (
                  <span className="text-slate-600 ml-1.5">
                    — {pos.rec} · {Math.round(pos.conf * 100)}%
                  </span>
                )}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

interface DebateFeedProps {
  status: RunStatusResponse;
  memoVersions: MemoVersion[];
  problemStatement: string;
}

export default function DebateFeed({ status, memoVersions, problemStatement }: DebateFeedProps) {
  const { current_turn, status: s, feedback_round, guardrail_passed, final_memo } = status;

  const hasMemo = memoVersions.length > 0;
  const isTerminal = s === 'awaiting_review' || s === 'completed';

  const turn1Done = current_turn >= 2 || isTerminal;
  const turn1Active = !turn1Done && s === 'running';

  const showTurn2 = current_turn >= 2 || isTerminal;
  const turn2Done = isTerminal;
  const turn2Active = showTurn2 && !turn2Done && s === 'running';

  const modT1Done = turn1Done;

  const expertSummaries = final_memo?.expert_positions.map(p => ({
    role: p.agent_role,
    rec: p.recommendation,
    conf: p.confidence,
  }));

  const isReprocessing = s === 'running' && feedback_round > 0 && memoVersions.length <= feedback_round;

  return (
    <div className="space-y-4 pb-4 max-w-3xl mx-auto">
      {/* Problem */}
      <div className="rounded-2xl bg-white/[0.03] border border-white/[0.06] p-5">
        <p className="text-[10px] font-semibold text-indigo-400 uppercase tracking-widest mb-2">
          Problem Statement
        </p>
        <p className="text-sm text-slate-300 leading-relaxed">{problemStatement}</p>
      </div>

      {/* Running notice */}
      {s === 'running' && !isReprocessing && (
        <div className="rounded-xl bg-blue-500/5 border border-blue-500/15 px-4 py-3 flex items-center gap-2.5">
          <Loader2 className="w-3.5 h-3.5 text-blue-400 animate-spin shrink-0" />
          <p className="text-xs text-blue-300">
            Agents are deliberating — each run makes ~25 LLM calls across 3 expert agents, moderator, arbiter &amp; synthesizer.
            <span className="text-blue-400/60 ml-1">Typically 3–6 min.</span>
          </p>
        </div>
      )}

      {/* Phase progress */}
      <div className="rounded-2xl bg-white/[0.03] border border-white/[0.06] p-5 space-y-2.5">
        <PhaseRow icon="📚" label="Context Ingestion" done />

        <TurnBlock
          turn={1}
          done={turn1Done}
          active={turn1Active}
          expertSummaries={turn1Done ? expertSummaries : undefined}
        />

        {modT1Done && (
          <PhaseRow icon="⚖️" label="Moderator — Disagreement Scoring" done />
        )}

        {showTurn2 && (
          <TurnBlock
            turn={2}
            done={turn2Done}
            active={turn2Active}
            expertSummaries={turn2Done ? expertSummaries : undefined}
          />
        )}

        {(hasMemo || (isTerminal && !hasMemo)) && (
          <PhaseRow
            icon="🔮"
            label="Synthesizer — Decision Memo"
            done={hasMemo}
            active={!hasMemo && s === 'running'}
          />
        )}

        {guardrail_passed && (
          <PhaseRow icon="🛡️" label="Guardrail Check — Passed" done />
        )}
      </div>

      {/* Memo versions with feedback dividers */}
      {memoVersions.map((mv, idx) => (
        <div key={mv.version} className="space-y-3">
          {/* Feedback text shown before this version (if it's a revision) */}
          {mv.feedbackText && (
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 rounded-full bg-amber-500/20 flex items-center justify-center shrink-0 mt-0.5">
                <span className="text-xs">💬</span>
              </div>
              <div className="flex-1 rounded-xl bg-amber-500/5 border border-amber-500/15 px-4 py-3">
                <p className="text-[10px] font-semibold text-amber-500 uppercase tracking-widest mb-1">
                  Your Feedback — Round {mv.version - 1}
                </p>
                <p className="text-xs text-amber-300/80 leading-relaxed">{mv.feedbackText}</p>
              </div>
            </div>
          )}

          {/* Version label */}
          <div className="flex items-center gap-3">
            <div className="h-px bg-white/[0.05] flex-1" />
            <span className="text-[11px] font-medium text-slate-600 px-1">
              Decision Memo — Version {mv.version}
            </span>
            <div className="h-px bg-white/[0.05] flex-1" />
          </div>

          <MemoCard memo={mv.memo} version={mv.version} isLatest={idx === memoVersions.length - 1} />
        </div>
      ))}

      {/* Re-processing spinner */}
      {isReprocessing && (
        <div className="rounded-2xl bg-indigo-500/5 border border-indigo-500/20 p-4">
          <div className="flex items-center gap-2.5">
            <Loader2 className="w-4 h-4 text-indigo-400 animate-spin shrink-0" />
            <p className="text-sm text-indigo-300">
              Revision v{feedback_round + 1} in progress — agents re-deliberating…
            </p>
          </div>
        </div>
      )}

      {/* Completed banner */}
      {s === 'completed' && status.action_status && (
        <div className="rounded-2xl bg-emerald-500/8 border border-emerald-500/20 p-4">
          <div className="flex items-center gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <p className="text-sm text-emerald-300">
              {status.action_status === 'sent'
                ? 'Debate complete — memo sent to Slack ✓'
                : `Complete — ${status.action_status}`}
            </p>
          </div>
        </div>
      )}

      {/* Error banner */}
      {s === 'error' && status.error && (
        <div className="rounded-2xl bg-red-500/8 border border-red-500/20 p-4">
          <p className="text-sm text-red-400">
            <span className="font-semibold">Error: </span>
            {status.error}
          </p>
        </div>
      )}
    </div>
  );
}
