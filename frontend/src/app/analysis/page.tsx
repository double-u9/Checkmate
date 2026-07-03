'use client';

import { Brain, GitBranch, ListChecks } from 'lucide-react';
import AppShell from '@/components/layout/AppShell';
import ExplanationPanel from '@/components/analysis/ExplanationPanel';
import AnalysisBoard from '@/components/chess/AnalysisBoard';
import MoveList from '@/components/chess/MoveList';
import MoveNavigator from '@/components/chess/MoveNavigator';
import GlassCard from '@/components/ui/GlassCard';
import StatusBadge from '@/components/ui/StatusBadge';
import PositionControls from '@/features/analysis/PositionControls';
import { usePositionAnalysis } from '@/features/analysis/usePositionAnalysis';

export default function AnalysisPage() {
  const position = usePositionAnalysis();

  return (
    <AppShell
      title="Deep analysis"
      eyebrow="Engine studio"
      description="Compare candidate moves, inspect principal variations, and keep the board and coach explanation in one responsive analysis surface."
      status={<StatusBadge tone={position.isAnalyzing ? 'info' : 'neutral'}>{position.isAnalyzing ? 'Thinking' : 'Ready'}</StatusBadge>}
    >
      <div className="grid gap-5 2xl:grid-cols-[minmax(0,0.95fr)_minmax(420px,0.72fr)]">
        <section className="space-y-5">
          <PositionControls
            fenInput={position.fenInput}
            setFenInput={position.setFenInput}
            pgnInput={position.pgnInput}
            setPgnInput={position.setPgnInput}
            onSetFen={() => position.applyFen(position.fenInput)}
            onLoadPgn={() => position.applyPgn()}
            onAnalyze={() => void position.analyze()}
            isAnalysisEnabled={position.isAnalysisEnabled}
            onAnalysisEnabledChange={position.setAnalysisEnabled}
            isAnalyzing={position.isAnalyzing}
            error={position.error}
            compact
          />

          <ExplanationPanel analysis={position.analysis} isLoading={position.isAnalyzing} />

          <GlassCard hover={false} className="space-y-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-200/70">Candidate planning</p>
                <h2 className="mt-1 text-lg font-semibold text-white">Review checklist</h2>
              </div>
              <Brain className="h-5 w-5 text-cyan-200" aria-hidden="true" />
            </div>
            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-xl border border-slate-700/70 bg-slate-950/45 p-4">
                <GitBranch className="h-4 w-4 text-cyan-200" aria-hidden="true" />
                <p className="mt-3 text-sm font-semibold text-white">Main line</p>
                <p className="mt-1 text-sm leading-6 text-slate-400">Start from the best move, then compare the next engine line before committing.</p>
              </div>
              <div className="rounded-xl border border-slate-700/70 bg-slate-950/45 p-4">
                <ListChecks className="h-4 w-4 text-emerald-200" aria-hidden="true" />
                <p className="mt-3 text-sm font-semibold text-white">Risk check</p>
                <p className="mt-1 text-sm leading-6 text-slate-400">High-severity tactical alerts should reshape the candidate list.</p>
              </div>
            </div>
          </GlassCard>
        </section>

        <aside className="2xl:sticky 2xl:top-5 2xl:self-start">
          <GlassCard hover={false} disableMotion variant="solid" id="analysis-board" className="p-3 sm:p-4">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3 px-1">
              <div>
                <h2 className="text-base font-semibold text-white">Variation board</h2>
                <p className="mt-1 text-sm text-slate-400">Play candidate moves directly on the board.</p>
              </div>
              <StatusBadge tone="neutral">Interactive</StatusBadge>
            </div>
            <AnalysisBoard
              fen={position.fen}
              analysis={position.analysis}
              evalAnalysis={position.evalAnalysis}
              customSquareStyles={position.customSquareStyles}
              onDrop={position.onDrop}
              label="Deep analysis chess board"
            />
            <MoveNavigator
              moves={position.moves}
              currentPly={position.currentPly}
              onStart={position.goToStart}
              onPrevious={position.goToPrevious}
              onNext={position.goToNext}
              onEnd={position.goToEnd}
            />
          </GlassCard>

          <div className="mt-5">
            <MoveList
              moves={position.moves}
              currentPly={position.currentPly}
              analysis={position.evalAnalysis}
              onSelectPly={position.goToPly}
            />
          </div>
        </aside>
      </div>
    </AppShell>
  );
}
