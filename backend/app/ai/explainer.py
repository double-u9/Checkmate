"""Move Explainer — the Explainable Chess AI layer."""

import chess
from loguru import logger

from app.chess_engine.stockfish import get_shared_engine
from app.chess_engine.evaluator import PositionEvaluator
from app.ai.tactical_motifs import TacticalMotifDetector
from app.ai.strategic import StrategicAnalyzer
from app.ai.nlg import ChessNLG
from app.models.schemas import ExplanationResponse


class MoveExplainer:
    """
    Explains WHY a move is good or bad using:
    1. Tactical motif detection
    2. Strategic analysis
    3. Engine evaluation comparison
    4. Natural language generation
    """

    def __init__(self):
        self.evaluator = PositionEvaluator()
        self.motif_detector = TacticalMotifDetector()
        self.strategic = StrategicAnalyzer()
        self.nlg = ChessNLG()

    @property
    def engine(self):
        """Lazily access the shared Stockfish engine singleton."""
        return get_shared_engine()

    async def explain_move(
        self, fen: str, move_uci: str, depth: int = 20
    ) -> ExplanationResponse:
        """
        Generate a complete explanation for a specific move.

        Args:
            fen: Position FEN before the move
            move_uci: The move in UCI notation
            depth: Analysis depth

        Returns:
            ExplanationResponse with human-readable explanation
        """
        try:
            board = chess.Board(fen)
            move = chess.Move.from_uci(move_uci)
        except (ValueError, Exception) as e:
            raise ValueError(f"Invalid FEN or move: {e}")

        if move not in board.legal_moves:
            raise ValueError(f"Illegal move {move_uci} in position {fen}")

        move_san = board.san(move)
        is_white = board.turn == chess.WHITE

        # 1. Evaluate position BEFORE the move
        info_before = await self.engine.analyze(board, depth, num_lines=1)
        score_before, _ = self.evaluator.extract_score(info_before[0])

        # 2. Detect tactical motifs
        tactical_motifs = self.motif_detector.detect_motifs(board, move)

        # 3. Strategic analysis before and after
        strategy_before = self.strategic.analyze(board)

        # 4. Apply the move and evaluate AFTER
        board_after = board.copy()
        board_after.push(move)
        info_after = await self.engine.analyze(board_after, depth, num_lines=1)
        score_after, mate_after = self.evaluator.extract_score(info_after[0])

        strategy_after = self.strategic.analyze(board_after)

        # 5. Classify the move
        classification = self.evaluator.classify_move(score_before, score_after, is_white)

        # 6. Determine strategic ideas
        strategic_ideas = self._compare_strategies(strategy_before, strategy_after)

        # 7. Generate natural language explanation
        explanation = self.nlg.generate_move_explanation(
            move_san=move_san,
            classification=classification,
            tactical_motifs=tactical_motifs,
            strategic_ideas=strategic_ideas,
            score_before=score_before,
            score_after=score_after,
        )

        return ExplanationResponse(
            move_san=move_san,
            evaluation_before=round(score_before, 2),
            evaluation_after=round(score_after, 2),
            explanation=explanation,
            tactical_motifs=tactical_motifs,
            strategic_ideas=strategic_ideas,
            classification=classification,
        )

    def _compare_strategies(self, before: dict, after: dict) -> list[str]:
        """Compare strategic factors before and after a move to identify changes."""
        ideas = []

        # King safety change
        for color in ["white", "black"]:
            ks_before = before["king_safety"].get(color, {}).get("score", 5)
            ks_after = after["king_safety"].get(color, {}).get("score", 5)
            if ks_after < ks_before - 2:
                ideas.append(f"{color.capitalize()}'s king becomes more vulnerable")
            elif ks_after > ks_before + 2:
                ideas.append(f"{color.capitalize()}'s king safety improves")

        # Space change
        space_before = before["space"]
        space_after = after["space"]
        if space_after.get("advantage") != space_before.get("advantage"):
            ideas.append(f"Space control shifts to {space_after.get('advantage', 'unclear')}")

        # Piece activity
        for color in ["white", "black"]:
            mob_before = before["piece_activity"].get(color, {}).get("mobility", 0)
            mob_after = after["piece_activity"].get(color, {}).get("mobility", 0)
            if mob_after > mob_before + 5:
                ideas.append(f"{color.capitalize()}'s pieces become more active")

        # New themes
        new_themes = set(after.get("themes", [])) - set(before.get("themes", []))
        for theme in new_themes:
            ideas.append(f"Creates {theme}")

        return ideas[:4]
