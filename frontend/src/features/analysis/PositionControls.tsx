'use client';

import { FileText, ImageUp, Play, Check, ScanLine } from 'lucide-react';
import type { ChangeEvent } from 'react';
import Button from '@/components/ui/Button';
import GlassCard from '@/components/ui/GlassCard';
import StatusBadge from '@/components/ui/StatusBadge';
import { cn } from '@/lib/cn';

export default function PositionControls({
  fenInput,
  setFenInput,
  pgnInput,
  setPgnInput,
  onSetFen,
  onLoadPgn,
  onAnalyze,
  onUpload,
  isAnalysisEnabled,
  onAnalysisEnabledChange,
  isAnalyzing,
  error,
  uploadState,
  uploadMessage,
  compact = false,
}: {
  fenInput: string;
  setFenInput: (value: string) => void;
  pgnInput: string;
  setPgnInput: (value: string) => void;
  onSetFen: () => void;
  onLoadPgn: () => void;
  onAnalyze: () => void;
  onUpload?: (event: ChangeEvent<HTMLInputElement>) => void;
  isAnalysisEnabled: boolean;
  onAnalysisEnabledChange: (enabled: boolean) => void;
  isAnalyzing: boolean;
  error: string | null;
  uploadState?: 'idle' | 'detecting' | 'detected' | 'failed';
  uploadMessage?: string;
  compact?: boolean;
}) {
  return (
    <GlassCard id="position-controls" hover={false} className="command-card space-y-4">
      <div className="relative flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-200/70">Command center</p>
          <h2 className="mt-1 text-lg font-semibold text-white">Load, analyze, iterate</h2>
        </div>
        <div className="flex items-center gap-2 rounded-xl border border-slate-700/80 bg-slate-950/60 px-3 py-2 text-xs font-semibold text-slate-300">
          <ScanLine className="h-4 w-4 text-cyan-200" aria-hidden="true" />
          FEN / PGN / Vision
        </div>
      </div>

      <form
        className="relative space-y-3"
        onSubmit={(event) => {
          event.preventDefault();
          onSetFen();
        }}
      >
        <div className="flex flex-wrap items-center justify-between gap-2">
          <label htmlFor="fen-input" className="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-200/70">
            Position FEN
          </label>
          <button
            type="button"
            role="switch"
            aria-checked={isAnalysisEnabled}
            onClick={() => onAnalysisEnabledChange(!isAnalysisEnabled)}
            className="inline-flex shrink-0 items-center gap-2 rounded-full border border-slate-700 bg-slate-950/70 px-2 py-1 text-xs font-semibold text-slate-200 transition-colors hover:border-cyan-300/60 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cyan-300"
          >
            <span
              className={cn(
                'relative h-5 w-9 overflow-hidden rounded-full border transition-colors',
                isAnalysisEnabled ? 'border-lime-400/50 bg-lime-500/70' : 'border-slate-600 bg-slate-800',
              )}
            >
              <span
                className={cn(
                  'absolute top-1/2 h-4 w-4 -translate-y-1/2 rounded-full bg-slate-950 shadow transition-transform',
                  isAnalysisEnabled ? 'translate-x-[18px]' : 'translate-x-[2px]',
                )}
              />
            </span>
            <span className="whitespace-nowrap">Analysis {isAnalysisEnabled ? 'on' : 'off'}</span>
          </button>
        </div>

        <div className="grid gap-2 xl:grid-cols-[1fr_auto_auto]">
          <input
            id="fen-input"
            value={fenInput}
            onChange={(event) => setFenInput(event.target.value)}
            className="control-field min-h-10 px-3 py-2 font-mono text-xs"
            placeholder="Paste FEN notation"
            autoComplete="off"
            spellCheck={false}
            aria-describedby={error ? 'fen-error' : undefined}
          />
          <Button type="submit" variant="secondary" icon={<Check className="h-4 w-4" aria-hidden="true" />}>
            Set
          </Button>
          <Button
            variant="primary"
            icon={<Play className="h-4 w-4" aria-hidden="true" />}
            isLoading={isAnalyzing}
            onClick={onAnalyze}
            disabled={!isAnalysisEnabled}
          >
            {isAnalysisEnabled ? (isAnalyzing ? 'Analyzing' : 'Analyze') : 'Analysis off'}
          </Button>
        </div>
      </form>

      <form
        className="relative space-y-2"
        onSubmit={(event) => {
          event.preventDefault();
          onLoadPgn();
        }}
      >
        <label htmlFor="pgn-input" className="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-200/70">
          PGN
        </label>
        <div className="grid gap-2 xl:grid-cols-[1fr_auto]">
          <textarea
            id="pgn-input"
            value={pgnInput}
            onChange={(event) => setPgnInput(event.target.value)}
            className="control-field min-h-[84px] resize-y px-3 py-2 font-mono text-xs leading-5"
            placeholder="1. e4 e5 2. Nf3 Nc6"
            spellCheck={false}
            aria-label="PGN move text"
          />
          <Button type="submit" variant="secondary" icon={<FileText className="h-4 w-4" aria-hidden="true" />}>
            Load PGN
          </Button>
        </div>
        {!compact && <p className="text-xs text-slate-500">Load a PGN to navigate the game, then toggle analysis on when you want engine arrows and explanations.</p>}
      </form>

      {onUpload && (
        <div className="flex flex-wrap items-center gap-3">
          <label className="inline-flex min-h-10 cursor-pointer items-center justify-center gap-2 rounded-lg border border-purple-400/40 bg-purple-500/15 px-4 text-sm font-semibold text-purple-100 transition-colors hover:border-purple-300 hover:bg-purple-500/25 focus-within:outline focus-within:outline-2 focus-within:outline-offset-2 focus-within:outline-purple-300">
            <ImageUp className="h-4 w-4" aria-hidden="true" />
            Upload board image
            <input type="file" accept="image/png,image/jpeg,image/webp,image/bmp" onChange={onUpload} className="sr-only" />
          </label>
          {uploadMessage && (
            <StatusBadge tone={uploadState === 'failed' ? 'danger' : uploadState === 'detected' ? 'success' : 'info'} className="normal-case tracking-normal">
              {uploadMessage}
            </StatusBadge>
          )}
        </div>
      )}

      {error && (
        <div id="fen-error" role="alert" className="rounded-lg border border-red-400/30 bg-red-500/10 px-3 py-2 text-sm text-red-200">
          {error}
        </div>
      )}
    </GlassCard>
  );
}
