'use client';

import { ChevronLeft, ChevronRight, SkipBack, SkipForward } from 'lucide-react';
import Button from '@/components/ui/Button';
import type { MoveRecord } from '@/features/analysis/usePositionAnalysis';

export default function MoveNavigator({
  moves,
  currentPly,
  onStart,
  onPrevious,
  onNext,
  onEnd,
}: {
  moves: MoveRecord[];
  currentPly: number;
  onStart: () => void;
  onPrevious: () => void;
  onNext: () => void;
  onEnd: () => void;
}) {
  const move = moves[currentPly - 1];
  const activeMove = currentPly === 0 ? 'Start position' : `${move?.moveNumber}${move?.color === 'b' ? '...' : '.'} ${move?.san ?? 'Move'}`;
  const canGoBack = currentPly > 0;
  const canGoForward = currentPly < moves.length;

  return (
    <div className="mt-3 flex items-center justify-between gap-2 rounded-xl border border-slate-800 bg-slate-950/70 p-2">
      <div className="min-w-0 px-2">
        <p className="truncate text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Move navigator</p>
        <p className="truncate text-sm font-semibold text-slate-200">{activeMove}</p>
      </div>
      <div className="flex shrink-0 items-center gap-1">
        <Button variant="ghost" className="h-10 min-h-10 w-10 px-0" aria-label="Go to start" onClick={onStart} disabled={!canGoBack}>
          <SkipBack className="h-4 w-4" aria-hidden="true" />
        </Button>
        <Button variant="secondary" className="h-10 min-h-10 w-10 px-0" aria-label="Previous move" onClick={onPrevious} disabled={!canGoBack}>
          <ChevronLeft className="h-5 w-5" aria-hidden="true" />
        </Button>
        <Button variant="secondary" className="h-10 min-h-10 w-10 px-0" aria-label="Next move" onClick={onNext} disabled={!canGoForward}>
          <ChevronRight className="h-5 w-5" aria-hidden="true" />
        </Button>
        <Button variant="ghost" className="h-10 min-h-10 w-10 px-0" aria-label="Go to latest move" onClick={onEnd} disabled={!canGoForward}>
          <SkipForward className="h-4 w-4" aria-hidden="true" />
        </Button>
      </div>
    </div>
  );
}
