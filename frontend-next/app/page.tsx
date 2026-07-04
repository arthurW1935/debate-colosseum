'use client';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import LoginButton from '@/components/LoginButton';
import ThemeToggle from '@/components/ThemeToggle';
import { useThemeMode } from '@/components/useThemeMode';
import { isLoggedIn } from '@/lib/auth';
import { ArrowRight, BadgeCheck, BrainCircuit, Scale, Sparkles } from 'lucide-react';

const TAGLINES = [
  'Disagreement is the product.',
  'Pressure-test the move before the market does.',
  'Turn executive doubt into a board-ready memo.',
];

export default function PublicLandingPage() {
  const router = useRouter();
  const { theme, toggleTheme } = useThemeMode();

  useEffect(() => {
    if (isLoggedIn()) router.replace('/app');
  }, [router]);

  return (
    <main
      data-theme={theme}
      className="executive-shell flex min-h-screen items-center overflow-hidden px-6 py-10 text-[var(--text-primary)]"
    >
      <div className="absolute right-6 top-6 z-20">
        <ThemeToggle theme={theme} onToggle={toggleTheme} />
      </div>

      <section className="relative z-10 mx-auto grid w-full max-w-[88rem] grid-cols-1 items-center gap-16 lg:grid-cols-[minmax(0,1fr)_440px] xl:gap-36 2xl:gap-44">
        <div className="py-10">
          <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-[var(--border)] bg-[var(--surface)]/70 px-3 py-1.5 text-xs font-semibold text-[var(--text-secondary)] shadow-sm backdrop-blur">
            <Sparkles className="h-3.5 w-3.5 text-[var(--accent-strong)]" />
            Debate Colosseum
          </div>

          <h1 className="font-serif-memo max-w-3xl text-5xl font-semibold leading-[1.02] tracking-[-0.04em] text-[var(--text-primary)] sm:text-6xl lg:text-7xl">
            Disagreement is the product.
          </h1>

          <p className="mt-6 max-w-2xl text-lg leading-8 text-[var(--text-secondary)]">
            Debate Colosseum puts specialist AI agents in a structured argument so founders can test strategic moves before committing capital, hiring plans, or board attention.
          </p>

          <div className="mt-8 grid max-w-2xl grid-cols-1 gap-3 sm:grid-cols-3">
            {[
              ['Specialists debate', BrainCircuit],
              ['Risks are argued', Scale],
              ['Memo is drafted', BadgeCheck],
            ].map(([label, Icon]) => {
              const IconComponent = Icon as typeof BrainCircuit;
              return (
                <div
                  key={label as string}
                  className="glass-panel rounded-3xl px-4 py-4 text-sm font-semibold text-[var(--text-primary)]"
                >
                  <IconComponent className="mb-3 h-4 w-4 text-[var(--accent-strong)]" />
                  {label as string}
                </div>
              );
            })}
          </div>

          <div className="mt-10 space-y-3">
            {TAGLINES.map(item => (
              <div key={item} className="flex items-center gap-3 text-sm text-[var(--text-secondary)]">
                <span className="h-1.5 w-1.5 rounded-full bg-[var(--accent)]" />
                {item}
              </div>
            ))}
          </div>
        </div>

        <div className="glass-panel relative overflow-hidden rounded-[36px] p-6 shadow-[var(--shadow-soft)] sm:p-8">
          <div className="absolute right-6 top-6 rounded-full border border-[var(--border)] bg-[var(--surface-raised)] px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--text-tertiary)]">
            Private workspace
          </div>

          <div className="mb-9 flex h-14 w-14 items-center justify-center rounded-3xl bg-[var(--text-primary)] text-[var(--app-bg)]">
            <ArrowRight className="h-5 w-5" />
          </div>

          <p className="text-xs font-semibold uppercase tracking-[0.26em] text-[var(--accent-strong)]">
            Start planning
          </p>
          <h2 className="font-serif-memo mt-3 text-4xl font-semibold leading-tight tracking-[-0.03em] text-[var(--text-primary)]">
            Start planning your next move.
          </h2>
          <p className="mt-4 text-sm leading-6 text-[var(--text-secondary)]">
            Sign in to keep your decision history, refinements, and memo versions tied to your workspace.
          </p>

          <div className="mt-8">
            <LoginButton className="w-full justify-center rounded-2xl px-5 py-3.5" />
          </div>

          <div className="mt-8 rounded-3xl border border-[var(--border)] bg-[var(--surface)]/60 p-4">
            <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-[var(--text-tertiary)]">
              What happens next
            </p>
            <div className="mt-4 space-y-3 text-sm text-[var(--text-secondary)]">
              <p>1. Ask the decision you are testing.</p>
              <p>2. Specialists argue from finance, growth, and risk.</p>
              <p>3. You receive a serious decision memo to refine.</p>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
