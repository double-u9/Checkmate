'use client';

import { Crosshair, Gauge, ShieldCheck } from 'lucide-react';
import type { ReactNode } from 'react';
import { useState } from 'react';
import AppShell from '@/components/layout/AppShell';
import ExplanationPanel from '@/components/analysis/ExplanationPanel';
import AnalysisBoard from '@/components/chess/AnalysisBoard';
import BoardSettingsCard from '@/components/chess/BoardSettingsCard';
import EngineTelemetry from '@/components/chess/EngineTelemetry';
import MoveList from '@/components/chess/MoveList';
import MoveNavigator from '@/components/chess/MoveNavigator';
import GlassCard from '@/components/ui/GlassCard';
import StatusBadge from '@/components/ui/StatusBadge';
import PositionControls from '@/features/analysis/PositionControls';
import { usePositionAnalysis } from '@/features/analysis/usePositionAnalysis';

function formatScore(evaluation?: number, mateIn?: number | null) {
  if (evaluation === undefined) return 'Ready';
  if (mateIn !== null && mateIn !== undefined) return mateIn > 0 ? `M${mateIn}` : `-M${Math.abs(mateIn)}`;
  return `${evaluation >= 0 ? '+' : ''}${evaluation.toFixed(1)}`;
}

function StatCard({ label, value, detail, icon }: { label: string; value: string | number; detail: string; icon: ReactNode }) {
  return (
    <div className="group rounded-xl border border-slate-800 bg-slate-950/45 p-4 transition-colors hover:border-cyan-300/30 hover:bg-slate-900/60">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">{label}</p>
          <p className="mt-2 text-2xl font-semibold text-white">{value}</p>
        </div>
        <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-cyan-300/20 bg-cyan-400/10 text-cyan-200 transition-transform group-hover:-translate-y-0.5">{icon}</div>
      </div>
      <p className="mt-3 text-xs leading-5 text-slate-400">{detail}</p>
    </div>
  );
}

export default function Dashboard() {
  const position = usePositionAnalysis();
  const [boardOrientation, setBoardOrientation] = useState<'white' | 'black'>('white');
  const [showBestMoveArrow, setShowBestMoveArrow] = useState(true);
  const [showMoveAnnotations, setShowMoveAnnotations] = useState(true);
  const [showEvalBar, setShowEvalBar] = useState(true);

  return (
    <AppShell
      title="Chess workspace"
      eyebrow="Aethelred"
      description="A single responsive cockpit for FEN analysis, image detection, board interaction, Stockfish evaluation, and coach-style explanation."
      status={
        <StatusBadge tone={position.isPracticeThinking || position.isAnalyzing ? 'info' : position.error ? 'danger' : 'neutral'}>
          {position.isPracticeThinking ? 'Computer reply' : position.isAnalyzing ? 'Analyzing' : position.error ? 'Input issue' : 'Board ready'}
        </StatusBadge>
      }
    >
      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.1fr)_minmax(360px,0.9fr)]">
        <section className="space-y-5" aria-label="Primary chess workspace">
          <PositionControls
            fenInput={position.fenInput}
            setFenInput={position.setFenInput}
            pgnInput={position.pgnInput}
            setPgnInput={position.setPgnInput}
            onSetFen={() => position.applyFen(position.fenInput)}
            onLoadPgn={() => position.applyPgn()}
            onAnalyze={() => void position.analyze()}
            onUpload={position.detectImage}
            isAnalysisEnabled={position.isAnalysisEnabled}
            onAnalysisEnabledChange={position.setAnalysisEnabled}
            isAnalyzing={position.isAnalyzing}
            error={position.error}
            uploadState={position.uploadState}
            uploadMessage={position.uploadMessage}
          />

          <GlassCard hover={false} disableMotion variant="solid" id="board-area" className="board-stage p-3 sm:p-4">
            <div className="relative mb-4 flex flex-wrap items-center justify-between gap-3 px-1">
              <div>
                <h2 className="text-base font-semibold text-white">Interactive board</h2>
                <p className="mt-1 text-sm text-slate-400">Move a piece to auto-run the current position through the engine.</p>
              </div>
              <StatusBadge tone={position.isPracticeThinking || position.isAnalyzing ? 'info' : position.analysis ? 'info' : position.evalAnalysis ? 'warning' : 'neutral'}>
                {position.isPracticeThinking ? 'Computer thinking' : position.isAnalyzing ? 'Analyzing' : position.analysis ? 'Engine evaluated' : position.evalAnalysis ? 'Previous eval' : 'Awaiting analysis'}
              </StatusBadge>
            </div>
            <div className="relative space-y-3">
              <EngineTelemetry
                analysis={position.analysis}
                evalAnalysis={position.evalAnalysis}
                isAnalyzing={position.isAnalyzing}
                isStale={position.isAnalysisStale}
                currentPly={position.currentPly}
                totalMoves={position.moves.length}
              />
              <AnalysisBoard
                fen={position.fen}
                analysis={position.analysis}
                evalAnalysis={position.evalAnalysis}
                customSquareStyles={showMoveAnnotations ? position.customSquareStyles : {}}
                onDrop={position.onDrop}
                boardOrientation={boardOrientation}
                showBestMoveArrow={showBestMoveArrow}
                showEvalBar={showEvalBar}
                isDraggablePiece={position.canDragPiece}
              />
              <MoveNavigator
                moves={position.moves}
                currentPly={position.currentPly}
                onStart={position.goToStart}
                onPrevious={position.goToPrevious}
                onNext={position.goToNext}
                onEnd={position.goToEnd}
              />
            </div>
          </GlassCard>
        </section>

        <aside className="space-y-5">
          <ExplanationPanel analysis={position.analysis} isLoading={position.isAnalyzing} />
          <BoardSettingsCard
            orientation={boardOrientation}
            onFlipBoard={() => setBoardOrientation((current) => (current === 'white' ? 'black' : 'white'))}
            isAnalysisEnabled={position.isAnalysisEnabled}
            onAnalysisEnabledChange={position.setAnalysisEnabled}
            showBestMoveArrow={showBestMoveArrow}
            onShowBestMoveArrowChange={setShowBestMoveArrow}
            showMoveAnnotations={showMoveAnnotations}
            onShowMoveAnnotationsChange={setShowMoveAnnotations}
            showEvalBar={showEvalBar}
            onShowEvalBarChange={setShowEvalBar}
            isPracticeMode={position.isPracticeMode}
            onPracticeModeChange={position.setPracticeMode}
            isPracticeThinking={position.isPracticeThinking}
            practiceSide={position.practiceSide}
            practiceMessage={position.practiceMessage}
          />
          <MoveList
            moves={position.moves}
            currentPly={position.currentPly}
            analysis={position.evalAnalysis}
            onSelectPly={position.goToPly}
          />

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3 xl:grid-cols-1 2xl:grid-cols-3">
            <StatCard
              label="Evaluation"
              value={formatScore(position.evalAnalysis?.evaluation, position.evalAnalysis?.mate_in)}
              detail="White-positive Stockfish score for the current position."
              icon={<Gauge className="h-4 w-4" aria-hidden="true" />}
            />
            <StatCard
              label="Threats"
              value={position.analysis?.threats.length ?? 0}
              detail="Tactical threats detected in the latest analysis."
              icon={<Crosshair className="h-4 w-4" aria-hidden="true" />}
            />
            <StatCard
              label="Source"
              value={position.uploadState === 'detected' ? 'Vision' : 'Manual'}
              detail={position.uploadMessage || 'Board state came from direct input or piece movement.'}
              icon={<ShieldCheck className="h-4 w-4" aria-hidden="true" />}
            />
          </div>
        </aside>
      </div>
    </AppShell>
  );
}
