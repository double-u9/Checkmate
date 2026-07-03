"""Chess Analyzer — orchestrates Stockfish + evaluator + threats into full analysis."""

import chess
from loguru import logger

from app.chess_engine.stockfish import get_shared_engine
from app.chess_engine.evaluator import PositionEvaluator
from app.chess_engine.threats import ThreatDetector
from app.models.schemas import (
    AnalysisResponse,
    MoveEvaluation,
    ThreatInfo,
)


class ChessAnalyzer:
    """High-level chess position analyzer combining engine + threats + evaluation."""

    def __init__(self):
        self.evaluator = PositionEvaluator()
        self.threat_detector = ThreatDetector()

    @property
    def engine(self):
        """Lazily access the shared Stockfish engine singleton."""
        return get_shared_engine()

    async def analyze_position(
        self, fen: str, depth: int = 20, num_lines: int = 3
    ) -> AnalysisResponse:
        """
        Full analysis of a chess position.

        Args:
            fen: FEN string
            depth: Analysis depth
            num_lines: Number of principal variations

        Returns:
            Complete AnalysisResponse
        """
        try:
            board = chess.Board(fen)
        except ValueError as e:
            raise ValueError(f"Invalid FEN: {fen} — {e}")

        # Run Stockfish analysis
        analysis_results = await self.engine.analyze(board, depth, num_lines)

        # Extract main line evaluation
        main_info = analysis_results[0]
        score, mate_in = self.evaluator.extract_score(main_info)
        pv_moves = self.evaluator.get_pv_moves(main_info, board)
        position_type = self.evaluator.classify_position(board)

        # Best move
        best_move_obj = main_info.get("pv", [None])[0]
        if best_move_obj:
            best_san = board.san(best_move_obj)
            best_move = MoveEvaluation(
                move_uci=best_move_obj.uci(),
                move_san=best_san,
                score=score,
                mate_in=mate_in,
                is_best=True,
                classification="best",
            )
        else:
            best_move = MoveEvaluation(
                move_uci="0000", move_san="--", score=score,
                mate_in=mate_in, is_best=True, classification="best",
            )

        # Top lines
        top_lines = []
        for info in analysis_results:
            pv = info.get("pv", [])
            line_score, line_mate = self.evaluator.extract_score(info)
            line_moves = []
            temp_board = board.copy()
            for move in pv[:5]:
                try:
                    san = temp_board.san(move)
                    line_moves.append(MoveEvaluation(
                        move_uci=move.uci(),
                        move_san=san,
                        score=line_score,
                        mate_in=line_mate,
                    ))
                    temp_board.push(move)
                except (ValueError, Exception):
                    break
            if line_moves:
                top_lines.append(line_moves)

        # Detect threats
        raw_threats = self.threat_detector.detect_threats(board)
        threats = [
            ThreatInfo(
                type=t["type"],
                description=t["description"],
                severity=t["severity"],
                squares=t["squares"],
            )
            for t in raw_threats[:10]  # Limit
        ]

        # Strategic themes
        strategic_themes = self._detect_strategic_themes(board)

        # Generate explanation
        explanation = self._generate_explanation(
            board, score, mate_in, best_move, threats, strategic_themes, position_type
        )

        # Generate attack heatmap
        heatmap = self._generate_heatmap(board)

        return AnalysisResponse(
            fen=fen,
            evaluation=round(score, 2),
            mate_in=mate_in,
            best_move=best_move,
            top_lines=top_lines,
            threats=threats,
            explanation=explanation,
            strategic_themes=strategic_themes,
            position_type=position_type,
            heatmap=heatmap,
        )

    def _detect_strategic_themes(self, board: chess.Board) -> list[str]:
        """Identify strategic themes in the position."""
        themes = []

        # Pawn structure
        white_pawns = board.pieces(chess.PAWN, chess.WHITE)
        black_pawns = board.pieces(chess.PAWN, chess.BLACK)

        # Isolated pawns
        for sq in white_pawns:
            file = chess.square_file(sq)
            adjacent_files = [f for f in [file - 1, file + 1] if 0 <= f <= 7]
            has_adjacent = any(
                chess.square(f, r) in white_pawns
                for f in adjacent_files for r in range(8)
            )
            if not has_adjacent:
                themes.append("isolated pawn")
                break

        # Open files
        for file in range(8):
            white_on_file = any(chess.square(file, r) in white_pawns for r in range(8))
            black_on_file = any(chess.square(file, r) in black_pawns for r in range(8))
            if not white_on_file and not black_on_file:
                themes.append("open file")
                break

        # King safety
        for color in [chess.WHITE, chess.BLACK]:
            king_sq = board.king(color)
            if king_sq:
                king_file = chess.square_file(king_sq)
                if king_file in [0, 1, 6, 7]:
                    themes.append("castled king")
                elif king_file in [3, 4]:
                    themes.append("king in center")

        # Material imbalance
        w_material = sum(
            len(board.pieces(pt, chess.WHITE)) * v
            for pt, v in [(chess.PAWN, 1), (chess.KNIGHT, 3), (chess.BISHOP, 3),
                          (chess.ROOK, 5), (chess.QUEEN, 9)]
        )
        b_material = sum(
            len(board.pieces(pt, chess.BLACK)) * v
            for pt, v in [(chess.PAWN, 1), (chess.KNIGHT, 3), (chess.BISHOP, 3),
                          (chess.ROOK, 5), (chess.QUEEN, 9)]
        )
        diff = w_material - b_material
        if abs(diff) >= 3:
            themes.append("material imbalance")

        # Bishop pair
        if len(board.pieces(chess.BISHOP, chess.WHITE)) >= 2:
            themes.append("bishop pair advantage (White)")
        if len(board.pieces(chess.BISHOP, chess.BLACK)) >= 2:
            themes.append("bishop pair advantage (Black)")

        return list(set(themes))[:6]

    def _generate_explanation(
        self, board, score, mate_in, best_move, threats, themes, position_type
    ) -> str:
        """Generate a high-level explanation of the position."""
        parts = []

        # Overall assessment
        if mate_in is not None:
            if mate_in > 0:
                parts.append(f"White has a forced checkmate in {mate_in} moves.")
            else:
                parts.append(f"Black has a forced checkmate in {abs(mate_in)} moves.")
        elif score > 2.0:
            parts.append("White has a decisive advantage.")
        elif score > 0.5:
            parts.append("White has a clear advantage.")
        elif score > 0.2:
            parts.append("White has a slight edge.")
        elif score < -2.0:
            parts.append("Black has a decisive advantage.")
        elif score < -0.5:
            parts.append("Black has a clear advantage.")
        elif score < -0.2:
            parts.append("Black has a slight edge.")
        else:
            parts.append("The position is roughly equal.")

        # Best move recommendation
        side = "White" if board.turn == chess.WHITE else "Black"
        parts.append(f"The best move for {side} is {best_move.move_san}.")

        # Key threats
        critical = [t for t in threats if t.severity in ("critical", "high")]
        if critical:
            parts.append(f"Key threat: {critical[0].description}.")

        # Position type
        parts.append(f"This is a {position_type} position.")

        # Themes
        if themes:
            parts.append(f"Key themes: {', '.join(themes[:3])}.")

        return " ".join(parts)

    def _generate_heatmap(self, board: chess.Board) -> list[list[float]]:
        """Generate an 8x8 heatmap of square control (positive = White, negative = Black)."""
        heatmap = []
        for rank in range(7, -1, -1):  # 8 down to 1
            row = []
            for file in range(8):  # a to h
                sq = chess.square(file, rank)
                white_attacks = len(board.attackers(chess.WHITE, sq))
                black_attacks = len(board.attackers(chess.BLACK, sq))
                control = (white_attacks - black_attacks) / max(white_attacks + black_attacks, 1)
                row.append(round(control, 2))
            heatmap.append(row)
        return heatmap
