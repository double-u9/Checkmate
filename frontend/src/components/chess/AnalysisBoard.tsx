'use client';

import { useId, useMemo, type ComponentProps, type CSSProperties } from 'react';
import { Chessboard } from 'react-chessboard';
import EvalBar from '@/components/chess/EvalBar';
import type { AnalysisResponse } from '@/lib/types';

type BoardSquare = `${'a' | 'b' | 'c' | 'd' | 'e' | 'f' | 'g' | 'h'}${'1' | '2' | '3' | '4' | '5' | '6' | '7' | '8'}`;
type BoardOrientation = 'white' | 'black';
type DraggablePieceGuard = NonNullable<ComponentProps<typeof Chessboard>['isDraggablePiece']>;

const BOARD_SQUARE = /^[a-h][1-8]$/;

function isBoardSquare(square: string): square is BoardSquare {
  return BOARD_SQUARE.test(square);
}

function getBestMoveSquares(move?: string) {
  if (!move || move.length < 4) return [];

  const from = move.slice(0, 2);
  const to = move.slice(2, 4);

  if (!isBoardSquare(from) || !isBoardSquare(to)) return [];

  return [from, to] as const;
}

function squareCenter(square: BoardSquare, orientation: BoardOrientation) {
  const file = square.charCodeAt(0) - 97;
  const rank = Number(square[1]);

  if (orientation === 'black') {
    return {
      x: ((7 - file) + 0.5) * 12.5,
      y: (rank - 0.5) * 12.5,
    };
  }

  return {
    x: (file + 0.5) * 12.5,
    y: (8 - rank + 0.5) * 12.5,
  };
}

function BestMoveArrow({ move, orientation }: { move?: string; orientation: BoardOrientation }) {
  const markerId = useId().replace(/:/g, '');
  const squares = getBestMoveSquares(move);
  if (!squares.length) return null;

  const [from, to] = squares;
  const start = squareCenter(from, orientation);
  const end = squareCenter(to, orientation);
  const dx = end.x - start.x;
  const dy = end.y - start.y;
  const length = Math.hypot(dx, dy) || 1;
  const unit = { x: dx / length, y: dy / length };
  const normal = { x: -unit.y, y: unit.x };
  const tip = {
    x: end.x - unit.x * 3.4,
    y: end.y - unit.y * 3.4,
  };
  const base = {
    x: tip.x - unit.x * 8,
    y: tip.y - unit.y * 8,
  };
  const arrowEnd = {
    x: base.x,
    y: base.y,
  };
  const outlineLeft = { x: base.x + normal.x * 5.2, y: base.y + normal.y * 5.2 };
  const outlineRight = { x: base.x - normal.x * 5.2, y: base.y - normal.y * 5.2 };
  const headLeft = { x: base.x + normal.x * 3.6, y: base.y + normal.y * 3.6 };
  const headRight = { x: base.x - normal.x * 3.6, y: base.y - normal.y * 3.6 };
  const outlinePoints = `${tip.x},${tip.y} ${outlineLeft.x},${outlineLeft.y} ${outlineRight.x},${outlineRight.y}`;
  const headPoints = `${tip.x},${tip.y} ${headLeft.x},${headLeft.y} ${headRight.x},${headRight.y}`;
  const highlightStart = {
    x: start.x + normal.x * 0.72,
    y: start.y + normal.y * 0.72,
  };
  const highlightEnd = {
    x: arrowEnd.x + normal.x * 0.72,
    y: arrowEnd.y + normal.y * 0.72,
  };
  const shineLeft = { x: base.x + normal.x * 1.8, y: base.y + normal.y * 1.8 };

  return (
    <svg className="pointer-events-none absolute inset-0 z-20 h-full w-full" viewBox="0 0 100 100" aria-hidden="true">
      <defs>
        <linearGradient id={`${markerId}-glass`} x1={`${start.x}%`} y1={`${start.y}%`} x2={`${end.x}%`} y2={`${end.y}%`}>
          <stop offset="0%" stopColor="rgba(255, 255, 255, 0.78)" />
          <stop offset="42%" stopColor="rgba(125, 211, 252, 0.50)" />
          <stop offset="100%" stopColor="rgba(34, 211, 238, 0.58)" />
        </linearGradient>
        <linearGradient id={`${markerId}-shine`} x1={`${start.x}%`} y1={`${start.y}%`} x2={`${end.x}%`} y2={`${end.y}%`}>
          <stop offset="0%" stopColor="rgba(255, 255, 255, 0.84)" />
          <stop offset="100%" stopColor="rgba(255, 255, 255, 0.22)" />
        </linearGradient>
        <filter id={`${markerId}-soft-edge`} x="-30%" y="-30%" width="160%" height="160%">
          <feDropShadow dx="0" dy="1" stdDeviation="0.8" floodColor="rgb(2, 6, 23)" floodOpacity="0.38" />
          <feDropShadow dx="0" dy="0" stdDeviation="1.3" floodColor="rgb(103, 232, 249)" floodOpacity="0.28" />
        </filter>
      </defs>
      <line
        x1={start.x}
        y1={start.y}
        x2={arrowEnd.x}
        y2={arrowEnd.y}
        stroke="rgba(2, 6, 23, 0.34)"
        strokeLinecap="round"
        strokeWidth="6.4"
      />
      <polygon points={outlinePoints} fill="rgba(2, 6, 23, 0.34)" />
      <line
        x1={start.x}
        y1={start.y}
        x2={arrowEnd.x}
        y2={arrowEnd.y}
        stroke={`url(#${markerId}-glass)`}
        strokeLinecap="round"
        strokeWidth="4.2"
        opacity="0.64"
        filter={`url(#${markerId}-soft-edge)`}
      />
      <polygon points={headPoints} fill={`url(#${markerId}-glass)`} opacity="0.68" filter={`url(#${markerId}-soft-edge)`} />
      <line
        x1={highlightStart.x}
        y1={highlightStart.y}
        x2={highlightEnd.x}
        y2={highlightEnd.y}
        stroke={`url(#${markerId}-shine)`}
        strokeLinecap="round"
        strokeWidth="1.05"
        opacity="0.82"
      />
      <polygon points={`${tip.x},${tip.y} ${shineLeft.x},${shineLeft.y} ${base.x},${base.y}`} fill="rgba(255, 255, 255, 0.34)" opacity="0.72" />
    </svg>
  );
}

export default function AnalysisBoard({
  fen,
  analysis,
  evalAnalysis,
  customSquareStyles,
  onDrop,
  label = 'Interactive chess board',
  boardOrientation = 'white',
  showBestMoveArrow = true,
  showEvalBar = true,
  isDraggablePiece,
}: {
  fen: string;
  analysis: AnalysisResponse | null;
  evalAnalysis?: AnalysisResponse | null;
  customSquareStyles: Record<string, CSSProperties>;
  onDrop: (sourceSquare: string, targetSquare: string) => boolean;
  label?: string;
  boardOrientation?: BoardOrientation;
  showBestMoveArrow?: boolean;
  showEvalBar?: boolean;
  isDraggablePiece?: DraggablePieceGuard;
}) {
  const currentEval = evalAnalysis ?? analysis;
  const bestMove = useMemo(() => analysis?.best_move?.move_uci, [analysis?.best_move?.move_uci]);

  return (
    <div className="flex gap-3" aria-label={label}>
      {showEvalBar && <EvalBar evaluation={currentEval?.evaluation ?? 0} mateIn={currentEval?.mate_in ?? null} />}
      <div className="min-w-0 flex-1">
        <div className="chessboard-shell relative overflow-hidden rounded-xl border border-cyan-300/20 bg-slate-950 shadow-2xl">
          <Chessboard
            position={fen}
            onPieceDrop={onDrop}
            boardOrientation={boardOrientation}
            customDarkSquareStyle={{ backgroundColor: '#5f7d65' }}
            customLightSquareStyle={{ backgroundColor: '#d9c58b' }}
            customSquareStyles={customSquareStyles}
            customBoardStyle={{ borderRadius: 0 }}
            isDraggablePiece={isDraggablePiece}
            snapToCursor
            animationDuration={220}
          />
          {showBestMoveArrow && <BestMoveArrow move={bestMove} orientation={boardOrientation} />}
        </div>
      </div>
    </div>
  );
}
