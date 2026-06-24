'use client';
import { useState } from 'react';
import { DecisionMemo, ExpertAnalysis, RiskItem } from '@/types';
import { ChevronDown, ChevronUp, CheckCircle2, AlertTriangle, XCircle } from 'lucide-react';

const AGENT_ICON: Record<string, string> = { growth: '📈', finance: '💰', risk: '⚠️' };

const REC = {
  proceed: {
    label: 'PROCEED',
    textColor: 'text-emerald-400',
    border: 'border-emerald-500/25',
    bg: 'bg-emerald-500/8',
    pill: 'bg-emerald-500/15 border-emerald-500/30',
    Icon: CheckCircle2,
  },
  'proceed-with-caution': {
    label: 'PROCEED WITH CAUTION',
    textColor: 'text-amber-400',
    border: 'border-amber-500/25',
    bg: 'bg-amber-500/8',
    pill: 'bg-amber-500/15 border-amber-500/30',
    Icon: AlertTriangle,
  },
  'do-not-proceed': {
    label: 'DO NOT PROCEED',
    textColor: 'text-red-400',
    border: 'border-red-500/25',
    bg: 'bg-red-500/8',
    pill: 'bg-red-500/15 border-red-500/30',
    Icon: XCircle,
  },
} as const;

const SEVERITY_COLOR: Record<string, string> = {
  low: 'text-emerald-400',
  medium: 'text-yellow-400',
  high: 'text-orange-400',
  critical: 'text-red-400',
};

function RiskTable({ risks }: { risks: RiskItem[] }) {
  if (!risks.length) return null;
  return (
    <div>
      <h4 className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest mb-2">
        Risk Register
      </h4>
      <div className="rounded-lg border border-white/[0.06] overflow-hidden">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-white/[0.03] text-slate-500">
              <th className="text-left px-3 py-2 font-medium">Description</th>
              <th className="px-3 py-2 font-medium">Severity</th>
              <th className="px-3 py-2 font-medium">Likelihood</th>
              <th className="text-left px-3 py-2 font-medium">Mitigation</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.04]">
            {risks.map((r, i) => (
              <tr key={i} className="hover:bg-white/[0.02] transition-colors">
                <td className="px-3 py-2 text-slate-300">{r.description}</td>
                <td className={`px-3 py-2 text-center font-medium capitalize ${SEVERITY_COLOR[r.severity]}`}>
                  {r.severity}
                </td>
                <td className="px-3 py-2 text-center text-slate-400 capitalize">{r.likelihood}</td>
                <td className="px-3 py-2 text-slate-400">{r.mitigation ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ExpertCard({ analysis }: { analysis: ExpertAnalysis }) {
  const [open, setOpen] = useState(false);
  const cfg = REC[analysis.recommendation];
  const Icon = cfg.Icon;
  return (
    <div className="rounded-xl bg-white/[0.03] border border-white/[0.06] p-3.5">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2.5">
          <span className="text-lg">{AGENT_ICON[analysis.agent_role]}</span>
          <div>
            <p className="text-xs font-semibold text-white capitalize">{analysis.agent_role} Agent</p>
            <div className={`flex items-center gap-1 mt-0.5 text-[10px] font-medium ${cfg.textColor}`}>
              <Icon className="w-3 h-3" />
              {cfg.label}
            </div>
          </div>
        </div>
        <div className="text-right shrink-0">
          <p className="text-sm font-semibold text-white">{Math.round(analysis.confidence * 100)}%</p>
          <p className="text-[10px] text-slate-600">confidence</p>
        </div>
      </div>

      <p className="text-xs text-slate-400 mt-2.5 leading-relaxed">{analysis.summary}</p>

      {analysis.dissent_notes && (
        <div className="mt-2 px-2.5 py-2 rounded-lg bg-amber-500/8 border border-amber-500/20">
          <p className="text-[11px] text-amber-400">
            <span className="font-semibold">Dissent: </span>
            {analysis.dissent_notes}
          </p>
        </div>
      )}

      {open && analysis.key_assumptions.length > 0 && (
        <div className="mt-3">
          <p className="text-[10px] font-semibold text-slate-600 uppercase tracking-widest mb-1.5">
            Key Assumptions
          </p>
          <ul className="space-y-1">
            {analysis.key_assumptions.map((a, i) => (
              <li key={i} className="text-[11px] text-slate-400 flex gap-1.5">
                <span className="text-slate-700 shrink-0 mt-0.5">•</span>
                {a}
              </li>
            ))}
          </ul>
        </div>
      )}

      <button
        onClick={() => setOpen(!open)}
        className="mt-2.5 flex items-center gap-0.5 text-[11px] text-indigo-400 hover:text-indigo-300 transition-colors"
      >
        {open ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        {open ? 'Collapse' : 'Show assumptions'}
      </button>
    </div>
  );
}

interface MemoCardProps {
  memo: DecisionMemo;
  version: number;
  isLatest: boolean;
}

export default function MemoCard({ memo, version, isLatest }: MemoCardProps) {
  const [collapsed, setCollapsed] = useState(!isLatest);
  const cfg = REC[memo.recommendation];
  const Icon = cfg.Icon;

  return (
    <div className={`rounded-2xl border overflow-hidden ${cfg.border} ${collapsed ? '' : cfg.bg}`}>
      <div
        className={`flex items-center justify-between px-5 py-4 ${!isLatest ? 'cursor-pointer hover:bg-white/[0.02]' : ''}`}
        onClick={() => !isLatest && setCollapsed(c => !c)}
      >
        <div className="flex items-center gap-3 flex-wrap">
          <div className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${cfg.pill} ${cfg.textColor}`}>
            <Icon className="w-3.5 h-3.5" />
            {cfg.label}
          </div>
          <span className="text-sm text-slate-400">
            Confidence:{' '}
            <strong className="text-white font-semibold">
              {Math.round(memo.confidence * 100)}%
            </strong>
          </span>
          {memo.feedback_revision_count > 0 && (
            <span className="text-[11px] text-slate-500 italic">
              revision #{memo.feedback_revision_count}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-xs px-2 py-0.5 rounded-md bg-white/[0.06] text-slate-400 font-mono">
            v{version}
          </span>
          {!isLatest && (
            collapsed
              ? <ChevronDown className="w-4 h-4 text-slate-600" />
              : <ChevronUp className="w-4 h-4 text-slate-600" />
          )}
        </div>
      </div>

      {!collapsed && (
        <div className="px-5 pb-6 space-y-5 border-t border-white/[0.06] pt-5">
          {/* Executive Summary */}
          <div>
            <h3 className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest mb-2">
              Executive Summary
            </h3>
            <p className="text-sm text-slate-200 leading-relaxed">{memo.executive_summary}</p>
          </div>

          {/* Agreements & Disagreements */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="rounded-xl bg-emerald-500/5 border border-emerald-500/15 p-4">
              <h4 className="text-[10px] font-semibold text-emerald-500 uppercase tracking-widest mb-2.5">
                Key Agreements
              </h4>
              {memo.key_agreements.length ? (
                <ul className="space-y-1.5">
                  {memo.key_agreements.map((a, i) => (
                    <li key={i} className="text-xs text-slate-300 flex gap-2">
                      <span className="text-emerald-500 shrink-0 mt-0.5">✓</span>
                      {a}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-slate-600">None</p>
              )}
            </div>
            <div className="rounded-xl bg-red-500/5 border border-red-500/15 p-4">
              <h4 className="text-[10px] font-semibold text-red-400 uppercase tracking-widest mb-2.5">
                Key Disagreements
              </h4>
              {memo.key_disagreements.length ? (
                <ul className="space-y-1.5">
                  {memo.key_disagreements.map((d, i) => (
                    <li key={i} className="text-xs text-slate-300 flex gap-2">
                      <span className="text-red-400 shrink-0 mt-0.5">⚡</span>
                      {d}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-slate-600">None</p>
              )}
            </div>
          </div>

          {/* Arbitration */}
          {memo.arbitration_summary && (
            <div className="rounded-xl bg-purple-500/8 border border-purple-500/20 p-4">
              <h4 className="text-[10px] font-semibold text-purple-400 uppercase tracking-widest mb-2">
                Arbitration Summary
              </h4>
              <p className="text-xs text-slate-300 leading-relaxed">{memo.arbitration_summary}</p>
            </div>
          )}

          {/* Expert Positions */}
          {memo.expert_positions.length > 0 && (
            <div>
              <h3 className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest mb-3">
                Expert Positions
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {memo.expert_positions.map((p, i) => (
                  <ExpertCard key={i} analysis={p} />
                ))}
              </div>
            </div>
          )}

          {/* Risk Register */}
          <RiskTable risks={memo.risk_register} />

          {/* Next Steps */}
          {memo.next_steps.length > 0 && (
            <div>
              <h4 className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest mb-2.5">
                Next Steps
              </h4>
              <ol className="space-y-2">
                {memo.next_steps.map((s, i) => (
                  <li key={i} className="text-xs text-slate-300 flex gap-2.5">
                    <span className="text-indigo-400 font-mono font-semibold shrink-0 w-4">
                      {i + 1}.
                    </span>
                    {s}
                  </li>
                ))}
              </ol>
            </div>
          )}

          {memo.generated_at && (
            <p className="text-[10px] text-slate-700 pt-1">Generated {memo.generated_at}</p>
          )}
        </div>
      )}
    </div>
  );
}
