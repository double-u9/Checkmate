"""Move predictor — predicts opponent's likely next moves."""

import chess
import chess.pgn
import io
from collections import Counter
from loguru import logger


class MovePredictor:
    """
    Predicts likely next moves based on:
    1. Opening book knowledge
    2. Historical move patterns
    3. Position-based heuristics
    """

    # Common opening moves
    COMMON_OPENINGS = {
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq -": [
            ("e2e4", 0.35, "King's Pawn — the most popular opening move"),
            ("d2d4", 0.30, "Queen's Pawn — solid and strategic"),
            ("g1f3", 0.15, "Réti Opening — flexible and modern"),
            ("c2c4", 0.12, "English Opening — positional approach"),
        ],
    }

    async def predict(
        self,
        fen: str,
        move_history: list[str] | None = None,
        player_style: str = "universal",
    ) -> list[dict]:
        """
        Predict likely next moves.

        Args:
            fen: Current position
            move_history: Previous moves in UCI notation
            player_style: Player's classified style

        Returns:
            List of {move, probability, reasoning} dicts
        """
        board = chess.Board(fen)
        predictions = []

        # Check opening book
        fen_key = " ".join(fen.split(" ")[:4])  # Position part only
        if fen_key in self.COMMON_OPENINGS:
            return [
                {"move": m, "probability": p, "reasoning": r}
                for m, p, r in self.COMMON_OPENINGS[fen_key]
            ]

        # Heuristic predictions based on style
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return []

        scored_moves = []
        for move in legal_moves:
            score = self._score_move(board, move, player_style)
            san = board.san(move)
            scored_moves.append((move, score, san))

        # Sort by score and normalize to probabilities
        scored_moves.sort(key=lambda x: x[1], reverse=True)
        total_score = sum(s for _, s, _ in scored_moves) or 1

        for move, score, san in scored_moves[:5]:
            prob = score / total_score
            reasoning = self._explain_prediction(board, move, player_style)
            predictions.append({
                "move": move.uci(),
                "move_san": san,
                "probability": round(prob, 3),
                "reasoning": reasoning,
            })

        return predictions

    def _score_move(self, board: chess.Board, move: chess.Move, style: str) -> float:
        """Score a move based on player style and position heuristics."""
        score = 1.0
        piece = board.piece_at(move.from_square)

        # Captures are likely for aggressive players
        if board.is_capture(move):
            score += 2.0 if style == "attacker" else 1.0

        # Checks
        board.push(move)
        if board.is_check():
            score += 3.0 if style == "attacker" else 1.5
        board.pop()

        # Center control
        to_file = chess.square_file(move.to_square)
        to_rank = chess.square_rank(move.to_square)
        if 2 <= to_file <= 5 and 2 <= to_rank <= 5:
            score += 1.5 if style == "positional" else 0.8

        # Development moves (in opening)
        if board.fullmove_number <= 10 and piece:
            if piece.piece_type in (chess.KNIGHT, chess.BISHOP):
                score += 2.0

        # Castling
        if board.is_castling(move):
            score += 2.5

        # Pawn pushes for space
        if piece and piece.piece_type == chess.PAWN:
            score += 0.5

        return max(score, 0.1)

    def _explain_prediction(self, board: chess.Board, move: chess.Move, style: str) -> str:
        """Generate a brief explanation for why this move is predicted."""
        reasons = []
        piece = board.piece_at(move.from_square)

        if board.is_capture(move):
            reasons.append("captures material")
        if board.is_castling(move):
            reasons.append("improves king safety")

        board.push(move)
        if board.is_check():
            reasons.append("gives check")
        board.pop()

        if piece and piece.piece_type in (chess.KNIGHT, chess.BISHOP) and board.fullmove_number <= 10:
            reasons.append("develops a piece")

        if not reasons:
            reasons.append("consistent with player's style")

        return "Likely because it " + " and ".join(reasons)
