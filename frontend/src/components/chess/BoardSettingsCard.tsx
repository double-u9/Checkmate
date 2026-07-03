'use client';

import { Bot, FlipHorizontal2, Gauge, LineChart, PencilRuler, Swords } from 'lucide-react';
import Button from '@/components/ui/Button';
import GlassCard from '@/components/ui/GlassCard';
import { cn } from '@/lib/cn';

function Toggle({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className="flex w-full items-center justify-between gap-3 rounded-lg px-2 py-2 text-left text-sm text-slate-200 transition-colors hover:bg-slate-800/70 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cyan-300"
    >
      <span>{label}</span>
      <span
        className={cn(
          'relative h-6 w-11 rounded-full border transition-colors',
          checked ? 'border-lime-400/50 bg-lime-500/75' : 'border-slate-600 bg-slate-700',
        )}
      >
        <span
          className={cn(
            'absolute top-1/2 h-5 w-5 -translate-y-1/2 rounded-full bg-slate-950 shadow transition-transform',
            checked ? 'translate-x-[20px]' : 'translate-x-[2px]',
          )}
        />
      </span>
    </button>
  );
}

function SectionLabel({ children }: { children: string }) {
  return (
    <div className="flex items-center gap-3 py-2">
      <div className="h-px flex-1 bg-slate-800" />
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">{children}</p>
      <div className="h-px flex-1 bg-slate-800" />
    </div>
  );
}

export default function BoardSettingsCard({
  orientation,
  onFlipBoard,
  isAnalysisEnabled,
  onAnalysisEnabledChange,
  showBestMoveArrow,
  onShowBestMoveArrowChange,
  showMoveAnnotations,
  onShowMoveAnnotationsChange,
  showEvalBar,
  onShowEvalBarChange,
  isPracticeMode,
  onPracticeModeChange,
  isPracticeThinking,
  practiceSide,
  practiceMessage,
}: {
  orientation: 'white' | 'black';
  onFlipBoard: () => void;
  isAnalysisEnabled: boolean;
  onAnalysisEnabledChange: (checked: boolean) => void;
  showBestMoveArrow: boolean;
  onShowBestMoveArrowChange: (checked: boolean) => void;
  showMoveAnnotations: boolean;
  onShowMoveAnnotationsChange: (checked: boolean) => void;
  showEvalBar: boolean;
  onShowEvalBarChange: (checked: boolean) => void;
  isPracticeMode: boolean;
  onPracticeModeChange: (checked: boolean) => void;
  isPracticeThinking: boolean;
  practiceSide: 'w' | 'b';
  practiceMessage: string;
}) {
  return (
    <GlassCard hover={false} className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-200/70">Board config</p>
          <h2 className="mt-1 text-sm font-semibold text-white">Analysis display</h2>
        </div>
        <PencilRuler className="h-5 w-5 text-cyan-200" aria-hidden="true" />
      </div>

      <div className="grid grid-cols-2 gap-2">
        <Button variant="ghost" className="justify-start px-3" icon={<FlipHorizontal2 className="h-4 w-4" aria-hidden="true" />} onClick={onFlipBoard}>
          Flip board
        </Button>
        <div className="flex min-h-10 items-center justify-center rounded-lg border border-slate-700 bg-slate-950/60 px-3 text-sm text-slate-300">
          {orientation === 'white' ? 'White bottom' : 'Black bottom'}
        </div>
      </div>

      <SectionLabel>Display</SectionLabel>
      <div className="space-y-1">
        <Toggle label="Move annotations" checked={showMoveAnnotations} onChange={onShowMoveAnnotationsChange} />
        <Toggle label="Evaluation bars" checked={showEvalBar} onChange={onShowEvalBarChange} />
      </div>

      <SectionLabel>Computer Analysis</SectionLabel>
      <div className="space-y-1">
        <Toggle label="Computer analysis" checked={isAnalysisEnabled} onChange={onAnalysisEnabledChange} />
        <Toggle label="Best move arrow" checked={showBestMoveArrow} onChange={onShowBestMoveArrowChange} />
        <Toggle label="Practice with computer" checked={isPracticeMode} onChange={onPracticeModeChange} />
      </div>

      {isPracticeMode && (
        <div className="rounded-xl border border-emerald-300/25 bg-emerald-400/10 p-3 text-sm text-emerald-50">
          <div className="flex items-center gap-2 font-semibold">
            <Bot className="h-4 w-4" aria-hidden="true" />
            You play {practiceSide === 'w' ? 'White' : 'Black'}
          </div>
          <p className="mt-2 text-xs leading-5 text-emerald-100/80">
            {isPracticeThinking ? 'Computer is thinking...' : practiceMessage}
          </p>
        </div>
      )}

      <div className="grid grid-cols-3 gap-2 border-t border-slate-800 pt-4">
        <div className="rounded-lg border border-slate-800 bg-slate-950/50 p-3 text-center">
          <LineChart className="mx-auto h-4 w-4 text-cyan-200" aria-hidden="true" />
          <p className="mt-2 text-[11px] font-semibold text-slate-400">PV</p>
        </div>
        <div className="rounded-lg border border-slate-800 bg-slate-950/50 p-3 text-center">
          <Gauge className="mx-auto h-4 w-4 text-lime-200" aria-hidden="true" />
          <p className="mt-2 text-[11px] font-semibold text-slate-400">Eval</p>
        </div>
        <div className="rounded-lg border border-slate-800 bg-slate-950/50 p-3 text-center">
          <Swords className="mx-auto h-4 w-4 text-amber-200" aria-hidden="true" />
          <p className="mt-2 text-[11px] font-semibold text-slate-400">Threats</p>
        </div>
      </div>

    </GlassCard>
  );
}
