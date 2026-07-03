"""Stockfish engine wrapper — centralized singleton with proper lifecycle management.

This module provides a thread-safe, singleton Stockfish engine manager that:
- Maintains a single engine instance shared across all modules
- Provides proper startup/shutdown lifecycle hooks for FastAPI lifespan
- Uses asyncio.to_thread for non-blocking Stockfish calls
- Serializes access via asyncio.Lock to prevent concurrent engine corruption
"""

import chess
import chess.engine
import asyncio
from pathlib import Path
from typing import Optional
from loguru import logger

from app.config import get_settings


class StockfishEngine:
    """Async wrapper around the Stockfish chess engine.
    
    Uses a single process with proper lifecycle management.
    Access is serialized via asyncio.Lock since Stockfish processes
    are not thread-safe for concurrent analysis.
    """

    def __init__(self):
        self.settings = get_settings()
        self._engine: Optional[chess.engine.SimpleEngine] = None
        self._lock = asyncio.Lock()
        self._initialized = False

    def _get_engine(self) -> chess.engine.SimpleEngine:
        """Get or create the Stockfish engine instance (synchronous)."""
        if self._engine is None:
            sf_path = self.settings.stockfish_path

            # Try common paths
            paths_to_try = [
                sf_path,
                "stockfish",
                "/usr/games/stockfish",
                "/usr/local/bin/stockfish",
                r"C:\stockfish\stockfish.exe",
                r"C:\Program Files\Stockfish\stockfish.exe",
            ]

            for path in paths_to_try:
                try:
                    self._engine = chess.engine.SimpleEngine.popen_uci(path)
                    self._engine.configure({
                        "Threads": self.settings.stockfish_threads,
                        "Hash": self.settings.stockfish_hash_mb,
                    })
                    self._initialized = True
                    logger.info(f"Stockfish initialized: {path}")
                    return self._engine
                except (FileNotFoundError, Exception) as e:
                    logger.error(f"Error starting Stockfish at {path}: {type(e).__name__}: {e}")
                    continue

            raise RuntimeError(
                f"Stockfish not found. Tried: {paths_to_try}. "
                "Install Stockfish and set STOCKFISH_PATH in .env"
            )

        return self._engine

    async def analyze(
        self,
        board: chess.Board,
        depth: int = 20,
        num_lines: int = 3,
    ) -> list[chess.engine.InfoDict]:
        """
        Analyze a position with multi-PV.

        Args:
            board: python-chess Board object
            depth: Search depth
            num_lines: Number of principal variations

        Returns:
            List of analysis info dicts
        """
        async with self._lock:
            return await asyncio.to_thread(
                self._analyze_sync, board, depth, num_lines
            )

    def _analyze_sync(
        self, board: chess.Board, depth: int, num_lines: int
    ) -> list[chess.engine.InfoDict]:
        """Synchronous analysis."""
        engine = self._get_engine()
        result = engine.analyse(
            board,
            chess.engine.Limit(depth=depth),
            multipv=num_lines,
        )
        return result if isinstance(result, list) else [result]

    async def get_best_move(self, board: chess.Board, depth: int = 20) -> chess.Move:
        """Get the best move for the current position."""
        async with self._lock:
            return await asyncio.to_thread(self._best_move_sync, board, depth)

    def _best_move_sync(self, board: chess.Board, depth: int) -> chess.Move:
        """Synchronous best move."""
        engine = self._get_engine()
        result = engine.play(board, chess.engine.Limit(depth=depth))
        return result.move

    def close(self):
        """Shutdown the engine process cleanly."""
        if self._engine:
            try:
                self._engine.quit()
            except Exception as e:
                logger.warning(f"Error closing Stockfish: {e}")
            finally:
                self._engine = None
                self._initialized = False
                logger.info("Stockfish engine closed")

    @property
    def is_initialized(self) -> bool:
        return self._initialized


# ─── Centralized Singleton ──────────────────────────────────────────

_shared_engine: Optional[StockfishEngine] = None


def get_shared_engine() -> StockfishEngine:
    """Get the shared Stockfish engine singleton.
    
    All modules (analysis routes, websocket, explainer, games) should use this
    instead of creating their own StockfishEngine instances. This prevents
    spawning multiple Stockfish processes and the associated memory waste.
    """
    global _shared_engine
    if _shared_engine is None:
        _shared_engine = StockfishEngine()
    return _shared_engine


async def shutdown_engine():
    """Shutdown the shared engine. Called during FastAPI lifespan shutdown."""
    global _shared_engine
    if _shared_engine is not None:
        _shared_engine.close()
        _shared_engine = None
        logger.info("Shared Stockfish engine shut down")
