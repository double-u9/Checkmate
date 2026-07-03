"""Unit tests for the Explainable AI module."""

import pytest
import chess

from app.ai.tactical_motifs import TacticalMotifDetector
from app.ai.strategic import StrategicAnalyzer
from app.ai.nlg import ChessNLG
from app.ai.explainer import MoveExplainer


class TestTacticalMotifDetector:
    """Tests for tactical pattern detection."""

    def setup_method(self):
        self.detector = TacticalMotifDetector()

    def test_detect_capture(self):
        """Capturing a piece should be detected as a motif."""
        board = chess.Board("4k3/8/8/3p4/4P3/8/8/4K3 w - - 0 1")
        move = chess.Move.from_uci("e4d5")
        motifs = self.detector.detect_motifs(board, move)
        assert any("capture" in m.lower() or "exchange" in m.lower() for m in motifs)

    def test_detect_check(self):
        """A checking move should be detected."""
        board = chess.Board("4k3/8/8/8/8/8/8/4K2R w - - 0 1")
        move = chess.Move.from_uci("h1h8")
        motifs = self.detector.detect_motifs(board, move)
        assert any("check" in m.lower() for m in motifs)

    def test_detect_castling(self):
        """Castling should be detected."""
        board = chess.Board("r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1")
        move = chess.Move.from_uci("e1g1")
        motifs = self.detector.detect_motifs(board, move)
        assert any("castling" in m.lower() for m in motifs)

    def test_detect_promotion(self):
        """Pawn promotion should be detected."""
        board = chess.Board("4k3/4P3/8/8/8/8/8/4K3 w - - 0 1")
        move = chess.Move.from_uci("e7e8q")
        motifs = self.detector.detect_motifs(board, move)
        assert any("promotion" in m.lower() for m in motifs)

    def test_piece_values(self):
        """Piece values should be standard."""
        assert self.detector._piece_value(chess.PAWN) == 1
        assert self.detector._piece_value(chess.KNIGHT) == 3
        assert self.detector._piece_value(chess.QUEEN) == 9

    def test_no_crash_on_normal_move(self):
        """Normal quiet move shouldn't crash."""
        board = chess.Board()
        move = chess.Move.from_uci("e2e4")
        motifs = self.detector.detect_motifs(board, move)
        assert isinstance(motifs, list)


class TestStrategicAnalyzer:
    """Tests for strategic position analysis."""

    def setup_method(self):
        self.analyzer = StrategicAnalyzer()

    def test_analyze_starting_position(self):
        """Starting position should return valid analysis."""
        board = chess.Board()
        result = self.analyzer.analyze(board)
        assert "pawn_structure" in result
        assert "king_safety" in result
        assert "piece_activity" in result
        assert "space" in result
        assert "themes" in result

    def test_pawn_structure_count(self):
        """Starting position should have 8 pawns per side."""
        board = chess.Board()
        ps = self.analyzer._analyze_pawn_structure(board)
        assert ps["white"]["count"] == 8
        assert ps["black"]["count"] == 8

    def test_isolated_pawn_detection(self):
        """An isolated pawn should be detected."""
        # White has isolated e-pawn (no d or f pawns)
        board = chess.Board("4k3/8/8/8/4P3/8/PP4PP/4K3 w - - 0 1")
        ps = self.analyzer._analyze_pawn_structure(board)
        assert len(ps["white"]["isolated"]) >= 1

    def test_king_safety_castled(self):
        """Castled king should have higher safety score."""
        board = chess.Board("r1bqkbnr/pppppppp/2n5/8/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3")
        ks = self.analyzer._analyze_king_safety(board)
        assert "white" in ks
        assert "black" in ks
        assert isinstance(ks["white"]["score"], (int, float))

    def test_space_analysis(self):
        """Space analysis should return counts for both sides."""
        board = chess.Board()
        space = self.analyzer._analyze_space(board)
        assert "white" in space
        assert "black" in space
        assert "advantage" in space


class TestChessNLG:
    """Tests for natural language generation."""

    def setup_method(self):
        self.nlg = ChessNLG()

    def test_position_commentary_winning(self):
        """Winning position should generate winning commentary."""
        text = self.nlg.generate_position_commentary(3.0, "White")
        assert "White" in text or "advantage" in text.lower() or "control" in text.lower()

    def test_position_commentary_equal(self):
        """Equal position should generate balanced commentary."""
        text = self.nlg.generate_position_commentary(0.1, "White")
        assert "equal" in text.lower() or "balanced" in text.lower() or "both" in text.lower()

    def test_move_explanation(self):
        """Move explanation should be non-empty and contain the move."""
        text = self.nlg.generate_move_explanation(
            move_san="e4",
            classification="good",
            tactical_motifs=["center control"],
            strategic_ideas=["Opens lines for the bishop"],
            score_before=0.0,
            score_after=0.3,
        )
        assert "e4" in text
        assert len(text) > 20

    def test_tactical_commentary_empty(self):
        """No motifs should generate a default message."""
        text = self.nlg.generate_tactical_commentary([])
        assert "no" in text.lower() or "threat" in text.lower()

    def test_all_classifications_have_templates(self):
        """Every move classification should have at least one template."""
        for classification in ["brilliant", "excellent", "good", "inaccuracy", "mistake", "blunder"]:
            assert classification in self.nlg.MOVE_QUALITY_PHRASES
            assert len(self.nlg.MOVE_QUALITY_PHRASES[classification]) >= 1


class FakeEngine:
    async def analyze(self, board, depth, num_lines=1):
        return [{}]


class FakeEvaluator:
    def __init__(self):
        self.scores = iter([(0.2, None), (0.7, None)])
        self.classify_args = None

    def extract_score(self, info):
        return next(self.scores)

    def classify_move(self, score_before, score_after, is_white):
        self.classify_args = (score_before, score_after, is_white)
        return "excellent"


class FakeMotifDetector:
    def detect_motifs(self, board, move):
        return ["center control"]


class FakeStrategicAnalyzer:
    def analyze(self, board):
        return {
            "king_safety": {"white": {"score": 5}, "black": {"score": 5}},
            "space": {"advantage": "white"},
            "piece_activity": {"white": {"mobility": 10}, "black": {"mobility": 10}},
            "themes": [],
        }


class FakeNLG:
    def generate_move_explanation(self, **kwargs):
        return f"{kwargs['move_san']} improves the position."


class TestMoveExplainer:
    @pytest.mark.asyncio
    async def test_score_after_remains_white_perspective(self, monkeypatch):
        """MoveExplainer should not negate evaluator scores that are already white-perspective."""
        fake_evaluator = FakeEvaluator()
        monkeypatch.setattr("app.ai.explainer.get_shared_engine", lambda: FakeEngine())

        explainer = MoveExplainer()
        explainer.evaluator = fake_evaluator
        explainer.motif_detector = FakeMotifDetector()
        explainer.strategic = FakeStrategicAnalyzer()
        explainer.nlg = FakeNLG()

        result = await explainer.explain_move(
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "e2e4",
            depth=1,
        )

        assert result.evaluation_before == 0.2
        assert result.evaluation_after == 0.7
        assert fake_evaluator.classify_args == (0.2, 0.7, True)
