"""Position evaluator — extracts scores, mate threats, and move quality."""

import chess
import chess.engine
from loguru import logger


class PositionEvaluator:
    """Extracts and normalizes evaluation data from Stockfish analysis."""

    @staticmethod
    def extract_score(info: chess.engine.InfoDict) -> tuple[float, int | None]:
        """
        Extract centipawn score and mate-in from analysis info.

        Returns:
            (score_in_pawns, mate_in_moves_or_None)
        """
        score = info.get("score")
        if score is None:
            return 0.0, None

        pov_score = score.white()  # Always from White's perspective

        if pov_score.is_mate():
            mate_in = pov_score.mate()
            # Convert mate to a large score for consistency
            score_val = 100.0 if mate_in > 0 else -100.0
            return score_val, mate_in
        else:
            cp = pov_score.score()
            return cp / 100.0 if cp is not None else 0.0, None

    @staticmethod
    def classify_move(
        score_before: float, score_after: float, is_white: bool
    ) -> str:
        """
        Classify move quality based on evaluation change.

        The evaluation change is from the perspective of the player making the move.
        """
        if is_white:
            delta = score_after - score_before
        else:
            delta = score_before - score_after  # Inverted for black

        if delta > 1.5:
            return "brilliant"
        elif delta > 0.5:
            return "excellent"
        elif delta > -0.1:
            return "good"
        elif delta > -0.5:
            return "inaccuracy"
        elif delta > -1.5:
            return "mistake"
        else:
            return "blunder"

    @staticmethod
    def classify_position(board: chess.Board) -> str:
        """Classify the game phase: opening, middlegame, or endgame."""
        piece_count = len(board.piece_map())

        # Check for queens
        has_queens = bool(board.queens)

        if board.fullmove_number <= 10:
            return "opening"
        elif piece_count <= 12 or (piece_count <= 16 and not has_queens):
            return "endgame"
        else:
            return "middlegame"

    @staticmethod
    def get_pv_moves(info: chess.engine.InfoDict, board: chess.Board) -> list[str]:
        """Extract the principal variation as SAN moves."""
        pv = info.get("pv", [])
        san_moves = []
        temp_board = board.copy()

        for move in pv[:10]:  # Limit to 10 moves
            try:
                san = temp_board.san(move)
                san_moves.append(san)
                temp_board.push(move)
            except (ValueError, Exception):
                break

        return san_moves
