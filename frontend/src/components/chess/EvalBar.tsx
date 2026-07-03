'use client';

import { motion } from 'framer-motion';

interface EvalBarProps {
  evaluation: number;
  mateIn: number | null;
}

export default function EvalBar({ evaluation, mateIn }: EvalBarProps) {
  const clampedEval = Math.max(-10, Math.min(10, evaluation));
  const whitePercent = 50 + (clampedEval / 10) * 50;
  const displayScore =
    mateIn !== null
      ? mateIn > 0
        ? `M${mateIn}`
        : `-M${Math.abs(mateIn)}`
      : evaluation > 0
        ? `+${evaluation.toFixed(1)}`
        : evaluation.toFixed(1);

  return (
    <div className="flex w-10 shrink-0 flex-col items-center gap-2 self-stretch" aria-label={`Evaluation ${displayScore}`}>
      <div className="w-full rounded-lg border border-slate-700 bg-slate-950 px-1 py-1 text-center text-[11px] font-semibold tabular-nums text-slate-100">
        {displayScore}
      </div>
      <div className="relative min-h-[260px] w-7 flex-1 overflow-hidden rounded-lg border border-slate-700 bg-[#141414]">
        <motion.div
          className="absolute bottom-0 left-0 right-0 bg-[#f3efe7]"
          initial={{ height: '50%' }}
          animate={{ height: `${whitePercent}%` }}
          transition={{ duration: 0.45, ease: 'easeInOut' }}
        />
        <div className="absolute inset-x-0 top-1/2 h-px bg-slate-500/60" aria-hidden="true" />
        <div className="absolute bottom-2 left-0 right-0 text-center text-[10px] font-bold text-[#141414]">W</div>
        <div className="absolute left-0 right-0 top-2 text-center text-[10px] font-bold text-white">B</div>
      </div>
    </div>
  );
}
