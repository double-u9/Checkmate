import type { ReactNode } from 'react';
import type { HTMLAttributes } from 'react';
import { cn } from '@/lib/cn';

type Tone = 'neutral' | 'success' | 'warning' | 'danger' | 'info';

const tones: Record<Tone, string> = {
  neutral: 'border-slate-600/50 bg-slate-800/70 text-slate-300',
  success: 'border-emerald-400/40 bg-emerald-500/15 text-emerald-200',
  warning: 'border-amber-400/40 bg-amber-500/15 text-amber-200',
  danger: 'border-red-400/40 bg-red-500/15 text-red-200',
  info: 'border-cyan-400/40 bg-cyan-500/15 text-cyan-200',
};

export default function StatusBadge({
  children,
  tone = 'neutral',
  dot = false,
  className,
  ...props
}: {
  children: ReactNode;
  tone?: Tone;
  dot?: boolean;
  className?: string;
} & HTMLAttributes<HTMLSpanElement>) {
  return (
    <span className={cn('inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide', tones[tone], className)} {...props}>
      {dot && <span className="h-1.5 w-1.5 rounded-full bg-current" aria-hidden="true" />}
      {children}
    </span>
  );
}
