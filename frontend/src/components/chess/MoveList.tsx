'use client';

import GlassCard from '@/components/ui/GlassCard';
import type { MoveRecord } from '@/features/analysis/usePositionAnalysis';
import { cn } from '@/lib/cn';
import type { AnalysisResponse } from '@/lib/types';

function formatScore(analysis: AnalysisResponse | null) {
  if (!analysis) return 'No eval';
  if (analysis.mate_in !== null && analysis.mate_in !== undefined) {
    return analysis.mate_in > 0 ? `M${analysis.mate_in}` : `-M${Math.abs(analysis.mate_in)}`;
  }
  return `${analysis.evaluation >= 0 ? '+' : ''}${analysis.evaluation.toFixed(1)}`;
}

export default function MoveList({
  moves,
  currentPly,
  analysis,
  onSelectPly,
}: {
  moves: MoveRecord[];
  currentPly: number;
  analysis: AnalysisResponse | null;
  onSelectPly: (ply: number) => void;
}) {
  const rows = [];
  for (let index = 0; index < moves.length; index += 2) {
    rows.push({
      number: moves[index].moveNumber,
      white: moves[index],
      black: moves[index + 1],
    });
  }

  return (
    <GlassCard hover={false} className="overflow-hidden p-0">
      <div className="flex items-center justify-between gap-3 border-b border-slate-800 bg-slate-950/35 px-4 py-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-200/70">Move list</p>
          <h2 className="mt-1 text-sm font-semibold text-white">Game notation</h2>
        </div>
        <div className="rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-1.5 text-sm font-semibold text-slate-200">
          {formatScore(analysis)}
        </div>
      </div>

      {moves.length === 0 ? (
        <div className="px-4 py-6 text-sm leading-6 text-slate-400">
          Load a PGN or make moves on the board to build a navigable game line.
        </div>
      ) : (
        <div className="max-h-[360px] overflow-y-auto">
          <div className="grid grid-cols-[3rem_minmax(0,1fr)_minmax(0,1fr)] text-sm">
            {rows.map((row) => (
              <div key={row.number} className="contents">
                <div className="border-b border-slate-900/90 bg-slate-950/25 px-4 py-2 text-right font-mono text-xs text-slate-500">{row.number}</div>
                {[row.white, row.black].map((move) => (
                  <button
                    key={move?.ply ?? `${row.number}-empty`}
                    type="button"
                    onClick={() => move && onSelectPly(move.ply)}
                    disabled={!move}
                    className={cn(
                      'min-h-10 border-b border-slate-900/90 px-3 py-2 text-left font-mono text-sm text-slate-300 transition-colors',
                      'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-cyan-300',
                      move && 'hover:bg-slate-800/70 hover:text-white',
                      move?.ply === currentPly && 'bg-gradient-to-r from-cyan-500/28 to-emerald-400/14 text-white shadow-[inset_3px_0_0_rgba(34,211,238,0.95)]',
                      !move && 'cursor-default',
                    )}
                  >
                    {move?.san ?? ''}
                  </button>
                ))}
              </div>
            ))}
          </div>
        </div>
      )}
    </GlassCard>
  );
}
