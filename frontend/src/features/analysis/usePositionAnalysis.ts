'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { ChangeEvent } from 'react';
import { Chess } from 'chess.js';
import { buildSquareStyles } from '@/lib/boardOverlays';
import { createSafeGame, normalizeFenInput, repairDetectedFen, STARTING_FEN, validateFen } from '@/lib/fen';
import api from '@/lib/api';
import type { AnalysisResponse } from '@/lib/types';

type UploadState = 'idle' | 'detecting' | 'detected' | 'failed';
type Side = 'w' | 'b';

export interface MoveRecord {
  ply: number;
  moveNumber: number;
  color: 'w' | 'b';
  san: string;
  uci: string;
  before: string;
  after: string;
}

type VerboseMove = {
  color: Side;
  from: string;
  to: string;
  promotion?: string;
  san: string;
  before: string;
  after: string;
};

function sideName(side: Side) {
  return side === 'w' ? 'White' : 'Black';
}

function hasGameEnded(game: Chess) {
  return Boolean((game as any).isGameOver?.() ?? (game as any).game_over?.() ?? false);
}

function recordFromMove(move: VerboseMove, ply: number): MoveRecord {
  return {
    ply,
    moveNumber: Math.floor((ply - 1) / 2) + 1,
    color: move.color,
    san: move.san,
    uci: `${move.from}${move.to}${move.promotion ?? ''}`,
    before: move.before,
    after: move.after,
  };
}

function buildMoveRecords(game: Chess): MoveRecord[] {
  return game.history({ verbose: true }).map((move, index) => recordFromMove(move, index + 1));
}

function pgnFromMoves(moves: MoveRecord[]) {
  if (!moves.length) return '';

  const chunks: string[] = [];
  for (let index = 0; index < moves.length; index += 2) {
    const white = moves[index];
    const black = moves[index + 1];
    chunks.push(`${white.moveNumber}. ${white.san}${black ? ` ${black.san}` : ''}`);
  }
  return chunks.join(' ');
}

export function usePositionAnalysis(initialFen = STARTING_FEN) {
  const [fen, setFen] = useState(initialFen);
  const [fenInput, setFenInput] = useState(initialFen);
  const [pgnInput, setPgnInput] = useState('');
  const [game, setGame] = useState(() => createSafeGame(initialFen));
  const [moves, setMoves] = useState<MoveRecord[]>([]);
  const [currentPly, setCurrentPly] = useState(0);
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [isAnalysisEnabled, setIsAnalysisEnabledState] = useState(true);
  const [isPracticeMode, setIsPracticeModeState] = useState(false);
  const [practiceSide, setPracticeSideState] = useState<Side>('w');
  const [isPracticeThinking, setIsPracticeThinking] = useState(false);
  const [practiceMessage, setPracticeMessage] = useState('Practice is off.');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadState, setUploadState] = useState<UploadState>('idle');
  const [uploadMessage, setUploadMessage] = useState('');
  const isAnalysisEnabledRef = useRef(isAnalysisEnabled);
  const isPracticeModeRef = useRef(false);
  const practiceSideRef = useRef<Side>('w');
  const analysisRequestRef = useRef(0);
  const practiceRequestRef = useRef(0);

  useEffect(() => {
    isAnalysisEnabledRef.current = isAnalysisEnabled;
  }, [isAnalysisEnabled]);

  useEffect(() => {
    isPracticeModeRef.current = isPracticeMode;
  }, [isPracticeMode]);

  useEffect(() => {
    practiceSideRef.current = practiceSide;
  }, [practiceSide]);

  const setPosition = useCallback((nextGame: Chess, nextMoves: MoveRecord[], nextPly: number, nextPgn?: string) => {
    const nextFen = nextGame.fen();
    setGame(nextGame);
    setFen(nextFen);
    setFenInput(nextFen);
    setMoves(nextMoves);
    setCurrentPly(nextPly);
    if (nextPgn !== undefined) setPgnInput(nextPgn);
  }, []);

  const syncPracticeSide = useCallback((nextGame: Chess) => {
    if (!isPracticeModeRef.current) return;
    const nextSide = nextGame.turn() as Side;
    practiceSideRef.current = nextSide;
    setPracticeSideState(nextSide);
    setPracticeMessage(`Practice on: you play ${sideName(nextSide)}.`);
  }, []);

  const analyzeFen = useCallback(async (targetFen: string) => {
    const validation = validateFen(targetFen);
    if (!validation.ok) {
      setError(validation.error);
      return false;
    }

    if (!isAnalysisEnabledRef.current) {
      setAnalysis(null);
      setIsAnalyzing(false);
      setError(null);
      return true;
    }

    const requestId = analysisRequestRef.current + 1;
    analysisRequestRef.current = requestId;
    setIsAnalyzing(true);
    setError(null);

    try {
      const result = await api.analyzePosition(validation.fen);
      if (analysisRequestRef.current === requestId && isAnalysisEnabledRef.current) {
        setAnalysis(result);
      }
      return true;
    } catch (err: any) {
      if (analysisRequestRef.current === requestId) {
        setError(err.message || 'Analysis failed. Check that the backend is online.');
      }
      return false;
    } finally {
      if (analysisRequestRef.current === requestId) {
        setIsAnalyzing(false);
      }
    }
  }, []);

  const applyFen = useCallback((nextFen: string) => {
    const normalizedFen = normalizeFenInput(nextFen);
    const validation = validateFen(normalizedFen);
    if (!validation.ok) {
      setFenInput(normalizedFen);
      setError(validation.error);
      return false;
    }

    setPosition(validation.game, [], 0, '');
    syncPracticeSide(validation.game);
    setAnalysis(null);
    setError(null);
    return true;
  }, [setPosition, syncPracticeSide]);

  const analyze = useCallback(async (customFen?: string) => {
    const targetFen = customFen || fenInput;
    const validation = validateFen(targetFen);
    if (!validation.ok) {
      setFenInput(normalizeFenInput(targetFen));
      setError(validation.error);
      return false;
    }

    setPosition(validation.game, moves, currentPly);
    return analyzeFen(validation.fen);
  }, [analyzeFen, currentPly, fenInput, moves, setPosition]);

  const applyPgn = useCallback((nextPgn = pgnInput) => {
    const text = nextPgn.trim();
    if (!text) {
      setError('Paste PGN moves before loading a game line.');
      return false;
    }

    try {
      const parsed = new Chess();
      parsed.loadPgn(text);
      const parsedMoves = buildMoveRecords(parsed);
      if (!parsedMoves.length) {
        setError('PGN loaded, but no legal moves were found.');
        return false;
      }

      setPosition(parsed, parsedMoves, parsedMoves.length, pgnFromMoves(parsedMoves));
      syncPracticeSide(parsed);
      setError(null);
      void analyzeFen(parsed.fen());
      return true;
    } catch (err: any) {
      setError(err.message || 'Invalid PGN. Check the move text and try again.');
      return false;
    }
  }, [analyzeFen, pgnInput, setPosition, syncPracticeSide]);

  const goToPly = useCallback((ply: number) => {
    const boundedPly = Math.max(0, Math.min(ply, moves.length));
    const targetFen = boundedPly === 0 ? moves[0]?.before ?? STARTING_FEN : moves[boundedPly - 1].after;
    const validation = validateFen(targetFen);
    if (!validation.ok) {
      setError(validation.error);
      return;
    }

    setGame(validation.game);
    setFen(validation.fen);
    setFenInput(validation.fen);
    setCurrentPly(boundedPly);
    syncPracticeSide(validation.game);
    setError(null);
    void analyzeFen(validation.fen);
  }, [analyzeFen, moves, syncPracticeSide]);

  const playComputerReply = useCallback(async (replyFromFen: string, baseMoves: MoveRecord[], requestId: number) => {
    const validation = validateFen(replyFromFen);
    if (!validation.ok) {
      setPracticeMessage(validation.error);
      setIsPracticeThinking(false);
      return;
    }

    if (hasGameEnded(validation.game)) {
      setPracticeMessage('Game over.');
      setIsPracticeThinking(false);
      void analyzeFen(validation.fen);
      return;
    }

    if (!isPracticeModeRef.current || validation.game.turn() === practiceSideRef.current) {
      setIsPracticeThinking(false);
      return;
    }

    setIsPracticeThinking(true);
    setPracticeMessage('Computer is calculating a reply...');

    try {
      const result = await api.analyzePosition(validation.fen, 16, 1);
      if (practiceRequestRef.current !== requestId || !isPracticeModeRef.current) return;

      const uci = result.best_move?.move_uci;
      if (!uci || uci.length < 4) throw new Error('Engine did not return a playable move.');

      const replyGame = createSafeGame(validation.fen);
      const reply = replyGame.move({
        from: uci.slice(0, 2),
        to: uci.slice(2, 4),
        promotion: uci[4] || 'q',
      });

      if (reply === null) throw new Error('Engine returned an illegal reply for this position.');

      const nextMoves = [...baseMoves, recordFromMove(reply, baseMoves.length + 1)];
      setPosition(replyGame, nextMoves, nextMoves.length, pgnFromMoves(nextMoves));
      setPracticeMessage(hasGameEnded(replyGame)
        ? `Computer played ${reply.san}. Game over.`
        : `Computer played ${reply.san}. Your turn as ${sideName(practiceSideRef.current)}.`);
      void analyzeFen(replyGame.fen());
    } catch (err: any) {
      if (practiceRequestRef.current === requestId) {
        setPracticeMessage(err.message || 'Computer reply failed. Try again from this position.');
        setError(err.message || 'Computer reply failed. Try again from this position.');
      }
    } finally {
      if (practiceRequestRef.current === requestId) setIsPracticeThinking(false);
    }
  }, [analyzeFen, setPosition]);

  const onDrop = useCallback((sourceSquare: string, targetSquare: string) => {
    if (isPracticeThinking) return false;
    if (isPracticeModeRef.current && game.turn() !== practiceSideRef.current) {
      setPracticeMessage('Wait for the computer reply before moving.');
      return false;
    }

    const gameCopy = createSafeGame(game.fen());

    try {
      const move = gameCopy.move({
        from: sourceSquare,
        to: targetSquare,
        promotion: 'q',
      });

      if (move === null) return false;

      const nextMoves = [...moves.slice(0, currentPly), recordFromMove(move, currentPly + 1)];
      const nextPgn = pgnFromMoves(nextMoves);

      setPosition(gameCopy, nextMoves, nextMoves.length, nextPgn);
      if (isPracticeModeRef.current) {
        const requestId = practiceRequestRef.current + 1;
        practiceRequestRef.current = requestId;
        setPracticeMessage(`You played ${move.san}. Computer is thinking...`);
        void playComputerReply(gameCopy.fen(), nextMoves, requestId);
      } else {
        void analyzeFen(gameCopy.fen());
      }
      return true;
    } catch {
      return false;
    }
  }, [analyzeFen, currentPly, game, isPracticeThinking, moves, playComputerReply, setPosition]);

  const detectImage = useCallback(async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.currentTarget.value = '';
    if (!file) return;

    setUploadState('detecting');
    setUploadMessage('Detecting board and pieces...');
    setError(null);
    try {
      const result = await api.detectBoard(file);
      if (!result.board_detected) {
        setUploadState('failed');
        setUploadMessage('No chessboard detected. Try a brighter, straighter image.');
        return;
      }

      const detected = repairDetectedFen(result.fen);
      setFenInput(detected.fen);

      if (detected.ok) {
        setPosition(detected.game, [], 0, '');
        syncPracticeSide(detected.game);
        setAnalysis(null);
        setError(null);
        setUploadState('detected');
        setUploadMessage(detected.repaired
          ? `Board detected at ${(result.confidence * 100).toFixed(1)}% confidence and normalized.`
          : `Board detected at ${(result.confidence * 100).toFixed(1)}% confidence.`);
        void analyzeFen(detected.fen);
      } else {
        setUploadState('failed');
        setUploadMessage('Board detected, but pieces are ambiguous. Edit the FEN and press Set.');
        setError(null);
      }
    } catch (err: any) {
      setUploadState('failed');
      setUploadMessage(err.message || 'Detection failed. Try PNG, JPEG, WebP, or BMP under 10 MB.');
    }
  }, [analyzeFen, setPosition, syncPracticeSide]);

  const setAnalysisEnabled = useCallback((enabled: boolean) => {
    setIsAnalysisEnabledState(enabled);
    isAnalysisEnabledRef.current = enabled;
    if (!enabled) {
      analysisRequestRef.current += 1;
      practiceRequestRef.current += 1;
      isPracticeModeRef.current = false;
      setIsPracticeModeState(false);
      setIsPracticeThinking(false);
      setPracticeMessage('Practice is off.');
      setAnalysis(null);
      setIsAnalyzing(false);
      setError(null);
      return;
    }
    void analyzeFen(fen);
  }, [analyzeFen, fen]);

  const setPracticeMode = useCallback((enabled: boolean) => {
    practiceRequestRef.current += 1;
    setIsPracticeModeState(enabled);
    isPracticeModeRef.current = enabled;
    setIsPracticeThinking(false);

    if (!enabled) {
      setPracticeMessage('Practice is off.');
      return;
    }

    setIsAnalysisEnabledState(true);
    isAnalysisEnabledRef.current = true;
    const userSide = game.turn() as Side;
    setPracticeSideState(userSide);
    practiceSideRef.current = userSide;
    setPracticeMessage(hasGameEnded(game) ? 'Practice on, but this position is already finished.' : `Practice on: you play ${sideName(userSide)}. Make your move.`);
    void analyzeFen(game.fen());
  }, [analyzeFen, game]);

  const canDragPiece = useCallback(({ piece }: { piece: string; sourceSquare: string }) => {
    if (isPracticeThinking) return false;
    if (!isPracticeMode) return true;
    const pieceSide = piece[0] === 'w' ? 'w' : 'b';
    return pieceSide === practiceSide && game.turn() === practiceSide;
  }, [game, isPracticeMode, isPracticeThinking, practiceSide]);

  const freshAnalysis = isAnalysisEnabled && analysis?.fen === fen ? analysis : null;
  const evalAnalysis = isAnalysisEnabled ? analysis : null;

  const customSquareStyles = useMemo(
    () => buildSquareStyles(game, freshAnalysis),
    [freshAnalysis, game],
  );

  return {
    fen,
    fenInput,
    pgnInput,
    game,
    moves,
    currentPly,
    analysis: freshAnalysis,
    evalAnalysis,
    isAnalysisStale: Boolean(isAnalysisEnabled && analysis && analysis.fen !== fen),
    isAnalysisEnabled,
    isPracticeMode,
    isPracticeThinking,
    practiceSide,
    practiceMessage,
    isAnalyzing,
    error,
    uploadState,
    uploadMessage,
    customSquareStyles,
    canGoBack: currentPly > 0,
    canGoForward: currentPly < moves.length,
    setFenInput,
    setPgnInput,
    setAnalysisEnabled,
    setPracticeMode,
    applyFen,
    applyPgn,
    analyze,
    goToPly,
    goToStart: () => goToPly(0),
    goToPrevious: () => goToPly(currentPly - 1),
    goToNext: () => goToPly(currentPly + 1),
    goToEnd: () => goToPly(moves.length),
    canDragPiece,
    onDrop,
    detectImage,
  };
}
