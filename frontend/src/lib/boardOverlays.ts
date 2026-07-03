/* Shared chessboard overlay utilities — DRY extraction from page.tsx and analysis/page.tsx */

import type { AnalysisResponse } from '@/lib/types';
import type { Chess } from 'chess.js';
import type React from 'react';

/** SVG badge icons for move classifications (chess.com-style) */
export const BADGE_SVGS = {
  best: `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="45" fill="%2384cc16" stroke="%233f6212" stroke-width="5"/><path d="M50 15 l10 30 h30 l-25 18 l10 30 l-25 -18 l-25 18 l10 -30 l-25 -18 h30 z" fill="white"/></svg>`,
  brilliant: `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="45" fill="%2306b6d4" stroke="%230891b2" stroke-width="5"/><text x="50" y="75" font-family="Arial" font-weight="bold" font-size="65" text-anchor="middle" fill="white">!!</text></svg>`,
  good: `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="45" fill="%233b82f6" stroke="%231d4ed8" stroke-width="5"/><text x="50" y="75" font-family="Arial" font-weight="bold" font-size="65" text-anchor="middle" fill="white">!</text></svg>`,
  inaccuracy: `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="45" fill="%23eab308" stroke="%23a16207" stroke-width="5"/><text x="50" y="75" font-family="Arial" font-weight="bold" font-size="60" text-anchor="middle" fill="white">?!</text></svg>`,
  mistake: `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="45" fill="%23f97316" stroke="%23c2410c" stroke-width="5"/><text x="50" y="75" font-family="Arial" font-weight="bold" font-size="65" text-anchor="middle" fill="white">?</text></svg>`,
  blunder: `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="45" fill="%23ef4444" stroke="%23b91c1c" stroke-width="5"/><text x="50" y="75" font-family="Arial" font-weight="bold" font-size="65" text-anchor="middle" fill="white">??</text></svg>`,
} as const;

const FILES = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'];

/**
 * Build custom square styles for chessboard overlays.
 * Consolidates check highlight, heatmap overlay, and best-move badges
 * into a single function used by both the main dashboard and analysis page.
 */
export function buildSquareStyles(
  game: Chess,
  analysis: AnalysisResponse | null
): Record<string, React.CSSProperties> {
  const styles: Record<string, React.CSSProperties> = {};

  // 1. King in Check/Checkmate highlight
  const isCheck = (typeof game.inCheck === 'function' ? game.inCheck() : (game as any).in_check?.()) || false;
  if (isCheck) {
    const boardArr = game.board();
    const turn = game.turn();
    for (let r = 0; r < 8; r++) {
      for (let c = 0; c < 8; c++) {
        const p = boardArr[r][c];
        if (p && p.type === 'k' && p.color === turn) {
          const sq = `${FILES[c]}${8 - r}`;
          styles[sq] = {
            background: 'radial-gradient(circle, rgba(255,0,0,0.8) 0%, rgba(255,0,0,0) 70%)',
          };
        }
      }
    }
  }

  // 2. Heatmap overlay
  if (analysis?.heatmap) {
    for (let r = 0; r < 8; r++) {
      for (let c = 0; c < 8; c++) {
        const heatVal = analysis.heatmap[r][c];
        if (heatVal !== 0) {
          const square = `${FILES[c]}${8 - r}`;
          styles[square] = {
            ...styles[square],
            backgroundColor: heatVal > 0
              ? `rgba(57, 255, 20, ${Math.abs(heatVal) * 0.3})`
              : `rgba(255, 7, 58, ${Math.abs(heatVal) * 0.3})`,
          };
        }
      }
    }
  }

  // 3. Best move highlight & badges
  if (analysis?.best_move?.move_uci) {
    const from = analysis.best_move.move_uci.slice(0, 2);
    const to = analysis.best_move.move_uci.slice(2, 4);
    const cls = analysis.best_move.classification as keyof typeof BADGE_SVGS;

    styles[from] = {
      ...styles[from],
      background: styles[from]?.background || 'radial-gradient(circle, rgba(34, 211, 238, 0.22), rgba(34, 211, 238, 0.06) 56%, transparent 76%)',
    };
    styles[to] = {
      ...styles[to],
      background: styles[to]?.background || 'radial-gradient(circle, rgba(52, 211, 153, 0.25), rgba(52, 211, 153, 0.07) 56%, transparent 76%)',
    };

    if (cls && BADGE_SVGS[cls]) {
      styles[to] = {
        ...styles[to],
        backgroundImage: `url('${BADGE_SVGS[cls]}')`,
        backgroundRepeat: 'no-repeat',
        backgroundPosition: 'top -3px right -3px',
        backgroundSize: '35%',
      };
    }
  }

  return styles;
}
