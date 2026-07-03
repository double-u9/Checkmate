import { Chess } from 'chess.js';

export const STARTING_FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';

export type FenValidation =
  | { ok: true; game: Chess; fen: string }
  | { ok: false; error: string };

export type DetectedFenRepair =
  | { ok: true; game: Chess; fen: string; repaired: boolean; message?: string }
  | { ok: false; error: string; fen: string };

const PIECES = 'pnbrqkPNBRQK';

export function normalizeFenInput(value: string) {
  return value
    .trim()
    .replace(/[–—−]/g, '-')
    .replace(/\s+/g, ' ');
}

function tryCreateGame(fen: string): FenValidation {
  try {
    const game = new Chess(fen);
    return { ok: true, game, fen: game.fen() };
  } catch {
    return {
      ok: false,
      error: 'Invalid FEN. Check piece placement, active color, castling rights, and move counters.',
    };
  }
}

function expandPlacement(placement: string) {
  const ranks = placement.split('/');
  if (ranks.length !== 8) return null;

  const board: string[][] = [];
  for (const rank of ranks) {
    const row: string[] = [];
    for (const char of rank) {
      if (/^[1-8]$/.test(char)) {
        row.push(...Array(Number(char)).fill(''));
      } else if (PIECES.includes(char)) {
        row.push(char);
      } else {
        return null;
      }
    }

    if (row.length < 8) row.push(...Array(8 - row.length).fill(''));
    board.push(row.slice(0, 8));
  }

  return board;
}

function compressPlacement(board: string[][]) {
  return board
    .map((row) => {
      let rank = '';
      let empty = 0;

      for (const piece of row) {
        if (!piece) {
          empty += 1;
        } else {
          if (empty) {
            rank += String(empty);
            empty = 0;
          }
          rank += piece;
        }
      }

      if (empty) rank += String(empty);
      return rank;
    })
    .join('/');
}

function ensureSingleKing(board: string[][], king: 'K' | 'k', preferredRank: number, preferredFile: number) {
  let found = false;
  for (let rank = 0; rank < 8; rank += 1) {
    for (let file = 0; file < 8; file += 1) {
      if (board[rank][file] === king) {
        if (found) board[rank][file] = '';
        found = true;
      }
    }
  }

  if (found) return;

  const candidates = [
    [preferredRank, preferredFile],
    [preferredRank, preferredFile - 1],
    [preferredRank, preferredFile + 1],
    [preferredRank, 3],
    [preferredRank, 5],
  ];

  const emptySquare = candidates.find(([rank, file]) => rank >= 0 && rank < 8 && file >= 0 && file < 8 && !board[rank][file]);
  const [rank, file] = emptySquare ?? [preferredRank, preferredFile];
  board[rank][file] = king;
}

export function validateFen(value: string): FenValidation {
  const fen = normalizeFenInput(value);

  if (!fen) {
    return { ok: false, error: 'Paste a FEN before updating the board.' };
  }

  const fields = fen.split(/\s+/);
  if (fields.length !== 6) {
    return {
      ok: false,
      error: 'FEN must include 6 fields: pieces, turn, castling, en passant, halfmove, and fullmove.',
    };
  }

  const primary = tryCreateGame(fen);
  if (primary.ok) return primary;

  const [, turn, castling, enPassant, halfmove, fullmove] = fields;
  const candidates = new Set<string>();
  const safeTurn = turn === 'b' ? 'b' : 'w';
  const safeHalfmove = /^\d+$/.test(halfmove) ? halfmove : '0';
  const safeFullmove = /^\d+$/.test(fullmove) && Number(fullmove) > 0 ? fullmove : '1';

  if (castling !== '-') candidates.add([fields[0], safeTurn, '-', enPassant, safeHalfmove, safeFullmove].join(' '));
  if (enPassant !== '-') candidates.add([fields[0], safeTurn, castling, '-', safeHalfmove, safeFullmove].join(' '));
  candidates.add([fields[0], safeTurn, '-', '-', safeHalfmove, safeFullmove].join(' '));

  for (const candidate of Array.from(candidates)) {
    const result = tryCreateGame(candidate);
    if (result.ok) return result;
  }

  return primary;
}

export function repairDetectedFen(value: string): DetectedFenRepair {
  const normalized = normalizeFenInput(value);
  const validation = validateFen(normalized);
  if (validation.ok) return { ...validation, repaired: false };

  const fields = normalized.split(/\s+/);
  const board = expandPlacement(fields[0] ?? '');
  if (!board) {
    return { ok: false, error: 'Vision detected a board, but the piece grid was unreadable.', fen: normalized };
  }

  ensureSingleKing(board, 'k', 0, 4);
  ensureSingleKing(board, 'K', 7, 4);

  const turn = fields[1] === 'b' ? 'b' : 'w';
  const halfmove = /^\d+$/.test(fields[4] ?? '') ? fields[4] : '0';
  const fullmove = /^\d+$/.test(fields[5] ?? '') && Number(fields[5]) > 0 ? fields[5] : '1';
  const repairedFen = `${compressPlacement(board)} ${turn} - - ${halfmove} ${fullmove}`;
  const repaired = validateFen(repairedFen);

  if (repaired.ok) {
    return {
      ...repaired,
      repaired: true,
      message: 'Board detected and normalized into a legal position. Review the FEN if any piece looks wrong.',
    };
  }

  return {
    ok: false,
    error: 'Vision detected a board, but pieces were too ambiguous to build a legal position.',
    fen: normalized,
  };
}

export function createSafeGame(fen = STARTING_FEN) {
  const result = validateFen(fen);
  return result.ok ? result.game : new Chess(STARTING_FEN);
}
