'use client';
import { DecisionMemo, ExpertAnalysis, RiskItem } from '@/types';
import { AlertTriangle, CheckCircle2, XCircle } from 'lucide-react';

const REC = {
  proceed: {
    label: 'Proceed',
    textColor: 'text-[var(--emerald)]',
    pill: 'bg-[var(--emerald)]/10 border-[var(--emerald)]/25',
    Icon: CheckCircle2,
  },
  'proceed-with-caution': {
    label: 'Proceed with caution',
    textColor: 'text-[var(--amber)]',
    pill: 'bg-[var(--amber)]/10 border-[var(--amber)]/25',
    Icon: AlertTriangle,
  },
  'do-not-proceed': {
    label: 'Do not proceed',
    textColor: 'text-[var(--danger)]',
    pill: 'bg-[var(--danger)]/10 border-[var(--danger)]/25',
    Icon: XCircle,
  },
} as const;

const SEVERITY_COLOR: Record<string, string> = {
  low: 'text-[var(--emerald)]',
  medium: 'text-[var(--amber)]',
  high: 'text-[var(--amber)]',
  critical: 'text-[var(--danger)]',
};

function RiskTable({ risks }: { risks: RiskItem[] }) {
  if (!risks.length) return null;
  return (
    <section>
      <h3 className="mb-3 text-[11px] font-semibold uppercase tracking-[0.2em] text-[var(--paper-muted)]">
        Risk Register
      </h3>
      <div className="overflow-hidden rounded-2xl border border-[var(--paper-border)]">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-[var(--paper-rule)] text-[var(--paper-muted)]">
              <th className="px-4 py-3 text-left font-semibold">Description</th>
              <th className="px-4 py-3 font-semibold">Severity</th>
              <th className="px-4 py-3 font-semibold">Likelihood</th>
              <th className="px-4 py-3 text-left font-semibold">Mitigation</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--paper-border)]">
            {risks.map((r, i) => (
              <tr key={i}>
                <td className="px-4 py-3 leading-5 text-[var(--paper-ink)]">{r.description}</td>
                <td className={`px-4 py-3 text-center font-semibold capitalize ${SEVERITY_COLOR[r.severity]}`}>
                  {r.severity}
                </td>
                <td className="px-4 py-3 text-center capitalize text-[var(--paper-muted)]">{r.likelihood}</td>
                <td className="px-4 py-3 text-[var(--paper-muted)]">{r.mitigation ?? '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function ExpertCard({ analysis }: { analysis: ExpertAnalysis }) {
  const cfg = REC[analysis.recommendation];
  const Icon = cfg.Icon;
  return (
    <div className="rounded-3xl border border-[var(--paper-border)] bg-[var(--paper-panel)] p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
        <p className="text-sm font-semibold capitalize text-[var(--paper-ink)]">
            {analysis.agent_role} specialist
          </p>
          <div className={`mt-2 inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-semibold ${cfg.pill} ${cfg.textColor}`}>
            <Icon className="h-3 w-3" />
            {cfg.label}
          </div>
        </div>
        <div className="text-right shrink-0">
          <p className="text-base font-semibold text-[var(--paper-ink)]">{Math.round(analysis.confidence * 100)}%</p>
          <p className="text-[10px] uppercase tracking-[0.16em] text-[var(--paper-muted)]">confidence</p>
        </div>
      </div>

      <p className="mt-4 text-sm leading-6 text-[var(--paper-muted)]">{analysis.summary}</p>

      {analysis.dissent_notes && (
        <div className="mt-4 rounded-2xl border border-[var(--amber)]/25 bg-[var(--amber)]/10 px-3 py-2">
          <p className="text-xs leading-5 text-[var(--paper-ink)]">
            <span className="font-semibold">Dissent: </span>
            {analysis.dissent_notes}
          </p>
        </div>
      )}
    </div>
  );
}

interface MemoCardProps {
  memo: DecisionMemo;
  version: number;
  isLatest: boolean;
}

export default function MemoCard({ memo, version, isLatest }: MemoCardProps) {
  const cfg = REC[memo.recommendation];
  const Icon = cfg.Icon;

  return (
    <article className="memo-paper flex h-full min-h-0 flex-col overflow-hidden rounded-[34px] border border-[var(--paper-border)]">
      <div className="h-2 bg-gradient-to-r from-[var(--accent-strong)] to-[var(--accent)]" />

      <div className="min-h-0 flex-1 overflow-y-auto px-7 py-7 sm:px-10">
        <header className="flex flex-col gap-5 border-b border-[var(--paper-border)] pb-7 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[var(--paper-muted)]">
              Decision Memo
            </p>
            <h2 className="font-serif-memo mt-3 text-4xl font-semibold leading-tight text-[var(--paper-ink)]">
              Strategic recommendation
            </h2>
            <p className="mt-3 text-sm text-[var(--paper-muted)]">
              Version {version}{isLatest ? ' · latest' : ''} · Confidence {Math.round(memo.confidence * 100)}%
            </p>
          </div>

          <div className={`inline-flex h-fit items-center gap-2 rounded-full border px-4 py-2 text-sm font-semibold ${cfg.pill} ${cfg.textColor}`}>
            <Icon className="h-4 w-4" />
            {cfg.label}
          </div>
        </header>

        <div className="space-y-7 py-7">
          <section>
            <h3 className="mb-3 text-[11px] font-semibold uppercase tracking-[0.2em] text-[var(--paper-muted)]">
              Executive summary
            </h3>
            <p className="font-serif-memo text-xl leading-8 text-[var(--paper-ink)]">
              {memo.executive_summary}
            </p>
          </section>

          <section className="rounded-3xl border border-[var(--paper-border)] bg-[var(--paper-panel)] p-6">
            <h3 className="mb-2 text-[11px] font-semibold uppercase tracking-[0.2em] text-[var(--paper-muted)]">
              Recommendation
            </h3>
            <p className="font-serif-memo text-xl font-semibold leading-7 text-[var(--paper-ink)]">
              {cfg.label}
            </p>
          </section>

          <section className="grid grid-cols-1 gap-5 lg:grid-cols-2">
            <div>
              <h3 className="mb-3 text-[11px] font-semibold uppercase tracking-[0.2em] text-[var(--paper-muted)]">
                Key agreements
              </h3>
              <ul className="space-y-3">
                {memo.key_agreements.length ? memo.key_agreements.map((a, i) => (
                  <li key={i} className="flex gap-3 text-sm leading-6 text-[var(--paper-ink)]">
                    <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--emerald)]" />
                    {a}
                  </li>
                )) : (
                  <li className="text-sm text-[var(--paper-muted)]">None recorded.</li>
                )}
              </ul>
            </div>
            <div>
              <h3 className="mb-3 text-[11px] font-semibold uppercase tracking-[0.2em] text-[var(--paper-muted)]">
                Key disagreements
              </h3>
              <ul className="space-y-3">
                {memo.key_disagreements.length ? memo.key_disagreements.map((d, i) => (
                  <li key={i} className="flex gap-3 text-sm leading-6 text-[var(--paper-ink)]">
                    <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--danger)]" />
                    {d}
                  </li>
                )) : (
                  <li className="text-sm text-[var(--paper-muted)]">None recorded.</li>
                )}
              </ul>
            </div>
          </section>

          {memo.arbitration_summary && (
            <section className="rounded-3xl border border-[var(--paper-border)] bg-[var(--paper-dispute)] p-6">
              <h3 className="mb-3 text-[11px] font-semibold uppercase tracking-[0.2em] text-[var(--paper-muted)]">
                Dispute handler summary
              </h3>
              <p className="font-serif-memo text-lg leading-7 text-[var(--paper-ink)]">
                {memo.arbitration_summary}
              </p>
            </section>
          )}

          {memo.expert_positions.length > 0 && (
            <section>
              <h3 className="mb-4 text-[11px] font-semibold uppercase tracking-[0.2em] text-[var(--paper-muted)]">
                Specialist positions
              </h3>
              <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
                {memo.expert_positions.map((p, i) => (
                  <ExpertCard key={i} analysis={p} />
                ))}
              </div>
            </section>
          )}

          <RiskTable risks={memo.risk_register} />

          {memo.next_steps.length > 0 && (
            <section>
              <h3 className="mb-4 text-[11px] font-semibold uppercase tracking-[0.2em] text-[var(--paper-muted)]">
                Next steps
              </h3>
              <ol className="space-y-3">
                {memo.next_steps.map((s, i) => (
                  <li key={i} className="flex gap-4 text-sm leading-6 text-[var(--paper-ink)]">
                    <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[var(--accent-soft)] text-xs font-semibold text-[var(--paper-ink)]">
                      {i + 1}
                    </span>
                    <span className="pt-0.5">{s}</span>
                  </li>
                ))}
              </ol>
            </section>
          )}

          {memo.generated_at && (
            <p className="border-t border-[var(--paper-border)] pt-5 text-xs text-[var(--paper-muted)]">
              Generated {memo.generated_at}
            </p>
          )}
        </div>
      </div>
    </article>
  );
}
