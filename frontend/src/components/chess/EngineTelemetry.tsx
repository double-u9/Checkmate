'use client';

import { Activity, Crosshair, GitBranch, Sparkles } from 'lucide-react';
import StatusBadge from '@/components/ui/StatusBadge';
import type { AnalysisResponse } from '@/lib/types';

function formatEval(analysis: AnalysisResponse | null) {
  if (!analysis) return 'Ready';
  if (analysis.mate_in !== null && analysis.mate_in !== undefined) {
    return analysis.mate_in > 0 ? `M${analysis.mate_in}` : `-M${Math.abs(analysis.mate_in)}`;
  }
  return `${analysis.evaluation >= 0 ? '+' : ''}${analysis.evaluation.toFixed(1)}`;
}

function firstLine(analysis: AnalysisResponse | null) {
  const line = analysis?.top_lines?.[0];
  if (!line?.length) return 'No principal variation yet';
  return line.slice(0, 6).map((move) => move.move_san).join(' ');
}

export default function EngineTelemetry({
  analysis,
  evalAnalysis,
  isAnalyzing,
  isStale,
  currentPly,
  totalMoves,
}: {
  analysis: AnalysisResponse | null;
  evalAnalysis: AnalysisResponse | null;
  isAnalyzing: boolean;
  isStale: boolean;
  currentPly: number;
  totalMoves: number;
}) {
  const visibleAnalysis = analysis ?? evalAnalysis;
  const tone = isAnalyzing ? 'info' : analysis ? 'success' : isStale ? 'warning' : 'neutral';

  return (
    <div className="engine-telemetry">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="engine-core" aria-hidden="true">
            <Activity className="h-4 w-4" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-200/70">Engine cockpit</p>
            <div className="mt-1 flex flex-wrap items-center gap-2">
              <span className="font-mono text-2xl font-semibold text-white">{formatEval(evalAnalysis)}</span>
              <StatusBadge tone={tone}>{isAnalyzing ? 'Calculating' : analysis ? 'Live' : isStale ? 'Previous eval' : 'Idle'}</StatusBadge>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-2 text-right text-xs">
          <div className="telemetry-pill">
            <Sparkles className="h-3.5 w-3.5 text-cyan-200" aria-hidden="true" />
            <span>{visibleAnalysis?.best_move?.move_san ?? '...'}</span>
          </div>
          <div className="telemetry-pill">
            <Crosshair className="h-3.5 w-3.5 text-rose-200" aria-hidden="true" />
            <span>{analysis?.threats.length ?? 0}</span>
          </div>
          <div className="telemetry-pill">
            <GitBranch className="h-3.5 w-3.5 text-emerald-200" aria-hidden="true" />
            <span>{currentPly}/{totalMoves}</span>
          </div>
        </div>
      </div>

      <div className="mt-4 rounded-xl border border-slate-800 bg-slate-950/50 p-3">
        <div className="flex flex-wrap items-center gap-2 text-xs text-slate-400">
          <span className="font-semibold uppercase tracking-[0.18em] text-slate-500">PV</span>
          <span className="font-mono text-slate-200">{firstLine(visibleAnalysis)}</span>
        </div>
        <div className="mt-3 h-1 overflow-hidden rounded-full bg-slate-800">
          <div className={isAnalyzing ? 'engine-progress is-active' : 'engine-progress'} />
        </div>
      </div>
    </div>
  );
}
