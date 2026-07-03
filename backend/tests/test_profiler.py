"""Unit tests for the Opponent Profiling module."""

import pytest
import numpy as np

from app.ai.opponent_profiler import OpponentProfiler
from app.ai.move_predictor import MovePredictor


SAMPLE_PGN = """[Event "Test"]
[Site "?"]
[Date "2024.01.01"]
[White "TestPlayer"]
[Black "Opponent"]
[Result "1-0"]
[ECO "B01"]

1. e4 d5 2. exd5 Qxd5 3. Nc3 Qa5 4. d4 Nf6 5. Nf3 Bf5 6. Bc4 e6 7. O-O Be7
8. Re1 O-O 9. a3 c6 10. Bd2 Qc7 11. Qe2 Nbd7 12. Rad1 Rfe8 13. Ng5 Nf8
14. f4 h6 15. Nf3 Ng4 16. h3 Nf6 17. Ne5 Nd5 18. Nxd5 cxd5 19. Bb3 Bd6
20. g4 Bh7 21. f5 Bxe5 22. dxe5 exf5 23. gxf5 d4 24. f6 g6 25. Bh6 Ng6
26. Qg4 Re6 27. Bg7 1-0"""


class TestOpponentProfiler:
    """Tests for opponent profiling."""

    def setup_method(self):
        self.profiler = OpponentProfiler()

    @pytest.mark.asyncio
    async def test_analyze_single_game(self):
        """Should produce a valid profile from a single game."""
        result = await self.profiler.analyze("TestPlayer", [SAMPLE_PGN])
        assert "style" in result
        assert "aggression_score" in result
        assert "risk_tolerance" in result
        assert 0 <= result["aggression_score"] <= 1
        assert 0 <= result["risk_tolerance"] <= 1

    @pytest.mark.asyncio
    async def test_analyze_empty_games(self):
        """Empty game list should return default profile."""
        result = await self.profiler.analyze("Nobody", [])
        assert result["style"] == "unknown"

    @pytest.mark.asyncio
    async def test_analyze_invalid_pgn(self):
        """Invalid PGN should be handled gracefully."""
        result = await self.profiler.analyze("TestPlayer", ["not a pgn"])
        assert result["style"] == "unknown"

    @pytest.mark.asyncio
    async def test_psychological_profile_generated(self):
        """Psychological profile should contain traits and recommendations."""
        result = await self.profiler.analyze("TestPlayer", [SAMPLE_PGN])
        psych = result.get("psychological_profile", {})
        assert "traits" in psych
        assert "recommendations" in psych
        assert len(psych["traits"]) >= 1

    def test_style_classification(self):
        """Style classification should return valid styles."""
        profiles = [
            {"aggression_score": 0.8, "tactical_preference": 0.7, "positional_preference": 0.3},
            {"aggression_score": 0.3, "tactical_preference": 0.3, "positional_preference": 0.7},
            {"aggression_score": 0.2, "tactical_preference": 0.2, "positional_preference": 0.4},
            {"aggression_score": 0.5, "tactical_preference": 0.5, "positional_preference": 0.5},
        ]
        expected = ["attacker", "positional", "defender", "universal"]

        for profile, expected_style in zip(profiles, expected):
            result = self.profiler._classify_style(profile)
            assert result == expected_style

    def test_feature_extraction(self):
        """Feature extraction should return numeric values."""
        features = self.profiler._extract_game_features(SAMPLE_PGN, "TestPlayer")
        assert features is not None
        assert features["total_moves"] > 0
        assert features["captures"] >= 0

    def test_count_material(self):
        """Material counting should be correct for starting position."""
        import chess
        board = chess.Board()
        material = self.profiler._count_material(board)
        # 8 pawns(1) + 2 knights(3) + 2 bishops(3) + 2 rooks(5) + 1 queen(9) = 39 per side
        assert material == 78  # Both sides combined

    def test_piece_value(self):
        """Piece values should be standard."""
        import chess
        assert self.profiler._piece_value(chess.PAWN) == 1
        assert self.profiler._piece_value(chess.QUEEN) == 9


class TestMovePredictor:
    """Tests for move prediction."""

    def setup_method(self):
        self.predictor = MovePredictor()

    @pytest.mark.asyncio
    async def test_predict_starting_position(self):
        """Starting position should return known opening predictions."""
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        predictions = await self.predictor.predict(fen)
        assert len(predictions) >= 1
        # e4 and d4 should be in top predictions
        moves = [p["move"] for p in predictions]
        assert "e2e4" in moves or "d2d4" in moves

    @pytest.mark.asyncio
    async def test_predict_has_probabilities(self):
        """Predictions should include probabilities that roughly sum to reasonable values."""
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        predictions = await self.predictor.predict(fen)
        if predictions:
            for pred in predictions:
                assert "probability" in pred
                assert "reasoning" in pred
                assert 0 <= pred["probability"] <= 1

    @pytest.mark.asyncio
    async def test_predict_checkmate_returns_empty(self):
        """Checkmated position should return no predictions."""
        fen = "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3"
        predictions = await self.predictor.predict(fen)
        # This is checkmate — no legal moves
        assert len(predictions) == 0
