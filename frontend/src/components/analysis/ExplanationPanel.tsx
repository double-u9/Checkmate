'use client';

import { AnimatePresence, motion } from 'framer-motion';
import { AlertTriangle, CheckCircle2, Diamond, LineChart, Sparkles, Star, Trophy, XCircle } from 'lucide-react';
import type { ComponentType } from 'react';
import GlassCard from '@/components/ui/GlassCard';
import StatusBadge from '@/components/ui/StatusBadge';
import { Skeleton } from '@/components/ui/Skeleton';
import type { AnalysisResponse, MoveClassification } from '@/lib/types';

interface ExplanationPanelProps {
  analysis: AnalysisResponse | null;
  isLoading?: boolean;
}

const CONFIG: Record<MoveClassification, { label: string; tone: 'success' | 'warning' | 'danger' | 'info'; icon: ComponentType<{ className?: string }> }> = {
  brilliant: { label: 'Brilliant', tone: 'info', icon: Diamond },
  excellent: { label: 'Excellent', tone: 'success', icon: Sparkles },
  good: { label: 'Good', tone: 'success', icon: CheckCircle2 },
  best: { label: 'Best', tone: 'info', icon: Star },
  inaccuracy: { label: 'Inaccuracy', tone: 'warning', icon: AlertTriangle },
  mistake: { label: 'Mistake', tone: 'warning', icon: XCircle },
  blunder: { label: 'Blunder', tone: 'danger', icon: XCircle },
};

function formatEval(analysis: AnalysisResponse) {
  if (analysis.mate_in !== null) return analysis.mate_in > 0 ? `M${analysis.mate_in}` : `-M${Math.abs(analysis.mate_in)}`;
  return `${analysis.evaluation >= 0 ? '+' : ''}${analysis.evaluation.toFixed(2)}`;
}

export default function ExplanationPanel({ analysis, isLoading }: ExplanationPanelProps) {
  if (isLoading) {
    return (
      <GlassCard id="explanation-panel" aria-live="polite">
        <div className="flex items-center justify-between">
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-6 w-20 rounded-full" />
        </div>
        <Skeleton className="mt-5 h-24 w-full" />
        <div className="mt-5 space-y-2">
          <Skeleton className="h-3 w-11/12" />
          <Skeleton className="h-3 w-4/5" />
          <Skeleton className="h-3 w-2/3" />
        </div>
      </GlassCard>
    );
  }

  if (!analysis) {
    return (
      <GlassCard id="explanation-panel" className="min-h-[220px]">
        <div className="flex min-h-[180px] flex-col items-center justify-center text-center">
          <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-lg border border-cyan-300/30 bg-cyan-400/10 text-cyan-200">
            <LineChart className="h-5 w-5" aria-hidden="true" />
          </div>
          <h2 className="text-sm font-semibold text-white">No engine readout yet</h2>
          <p className="mt-2 max-w-md text-sm leading-6 text-slate-400">
            Set a FEN, upload a board image, or move a piece to get best moves, threats, and coach-style explanation.
          </p>
        </div>
      </GlassCard>
    );
  }

  const config = CONFIG[analysis.best_move.classification] || CONFIG.good;
  const Icon = config.icon;

  return (
    <GlassCard id="explanation-panel" className="space-y-5" aria-live="polite">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-200/70">Coach analysis</p>
          <h2 className="mt-1 text-lg font-semibold text-white">Position explanation</h2>
        </div>
        <StatusBadge tone="info">{analysis.position_type}</StatusBadge>
      </div>

      <AnimatePresence mode="wait">
        {analysis.mate_in === 0 ? (
          <motion.div
            key="checkmate"
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-xl border border-red-400/40 bg-red-500/15 p-4"
          >
            <div className="flex items-center gap-3">
              <Trophy className="h-6 w-6 text-red-200" aria-hidden="true" />
              <div>
                <h3 className="font-semibold text-red-100">Checkmate on board</h3>
                <p className="text-sm text-red-200/80">{analysis.evaluation < 0 ? 'Black' : 'White'} has a forced win.</p>
              </div>
            </div>
          </motion.div>
        ) : (
          <motion.div
            key={analysis.best_move.move_san}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            className="rounded-xl border border-slate-700 bg-slate-950/55 p-4"
          >
            <div className="flex items-start gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-cyan-300/20 bg-cyan-400/10 text-cyan-200">
                <Icon className="h-5 w-5" aria-hidden="true" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-mono text-2xl font-semibold tracking-tight text-white">{analysis.best_move.move_san}</span>
                  <StatusBadge tone={config.tone}>{config.label}</StatusBadge>
                </div>
                <p className="mt-1 text-sm text-slate-400">Best move with evaluation {formatEval(analysis)}</p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <p className="text-sm leading-7 text-slate-300">{analysis.explanation}</p>

      {analysis.strategic_themes.length > 0 && (
        <section aria-labelledby="strategic-themes">
          <h3 id="strategic-themes" className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Strategic themes</h3>
          <div className="mt-3 flex flex-wrap gap-2">
            {analysis.strategic_themes.map((theme) => (
              <StatusBadge key={theme} tone="success">{theme}</StatusBadge>
            ))}
          </div>
        </section>
      )}

      {analysis.threats.length > 0 && (
        <section aria-labelledby="active-threats">
          <h3 id="active-threats" className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Active threats</h3>
          <div className="mt-3 space-y-2">
            {analysis.threats.slice(0, 4).map((threat, index) => (
              <div key={`${threat.type}-${index}`} className="rounded-lg border border-slate-700/70 bg-slate-950/45 p-3 text-sm text-slate-300">
                <StatusBadge tone={threat.severity === 'critical' || threat.severity === 'high' ? 'danger' : 'warning'}>
                  {threat.severity}
                </StatusBadge>
                <p className="mt-2 leading-6">{threat.description}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {analysis.top_lines.length > 0 && (
        <section aria-labelledby="top-lines">
          <h3 id="top-lines" className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Principal variations</h3>
          <div className="mt-3 space-y-2 font-mono text-xs">
            {analysis.top_lines.slice(0, 3).map((line, index) => (
              <div key={index} className="grid grid-cols-[1.5rem_1fr_auto] items-center gap-2 rounded-lg border border-slate-700/70 bg-slate-950/45 px-3 py-2 text-slate-400">
                <span className="font-semibold text-cyan-300">{index + 1}</span>
                <span className="truncate">{line.map((move) => move.move_san).join(' ')}</span>
                <span className="text-slate-500">{line[0]?.score >= 0 ? '+' : ''}{line[0]?.score.toFixed(1)}</span>
              </div>
            ))}
          </div>
        </section>
      )}
    </GlassCard>
  );
}
