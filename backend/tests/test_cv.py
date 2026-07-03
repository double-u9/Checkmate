"""Unit tests for the Computer Vision pipeline."""

import pytest
import numpy as np
import cv2

from app.cv.board_detector import BoardDetector
from app.cv.perspective import PerspectiveCorrector
from app.cv.grid_extractor import GridExtractor
from app.cv.piece_classifier import PieceClassifier, PIECE_CLASSES
from app.cv.fen_generator import FENGenerator


class TestBoardDetector:
    """Tests for board detection."""

    def setup_method(self):
        self.detector = BoardDetector()

    def test_fallback_detects_square_image(self):
        """A square image with a grid-like pattern should be detected."""
        # Create a synthetic chessboard-like image
        img = np.zeros((400, 400, 3), dtype=np.uint8)
        for r in range(8):
            for c in range(8):
                color = (200, 180, 140) if (r + c) % 2 == 0 else (80, 50, 30)
                y1, y2 = r * 50, (r + 1) * 50
                x1, x2 = c * 50, (c + 1) * 50
                img[y1:y2, x1:x2] = color

        corners = self.detector.detect(img)
        assert corners is not None
        assert corners.shape == (4, 2)

    def test_no_board_in_random_noise(self):
        """Random noise shouldn't reliably detect as a board."""
        img = np.random.randint(0, 255, (200, 300, 3), dtype=np.uint8)
        corners = self.detector.detect(img)
        # May or may not detect — just ensure no crash
        if corners is not None:
            assert corners.shape == (4, 2)

    def test_order_corners(self):
        """Corner ordering should be TL, TR, BR, BL."""
        pts = np.array([[100, 0], [0, 0], [0, 100], [100, 100]], dtype=np.float32)
        ordered = BoardDetector._order_corners(pts)
        # TL should have smallest sum
        assert ordered[0][0] + ordered[0][1] <= ordered[2][0] + ordered[2][1]


class TestPerspectiveCorrector:
    """Tests for perspective correction."""

    def setup_method(self):
        self.corrector = PerspectiveCorrector()

    def test_correct_returns_400x400(self):
        """Output should always be 400x400."""
        img = np.random.randint(0, 255, (500, 600, 3), dtype=np.uint8)
        corners = np.array([[50, 50], [550, 50], [550, 450], [50, 450]], dtype=np.float32)
        result = self.corrector.correct(img, corners)
        assert result.shape == (400, 400, 3)

    def test_identity_transform(self):
        """Corners matching image bounds should produce near-identity transform."""
        img = np.ones((400, 400, 3), dtype=np.uint8) * 128
        corners = np.array([[0, 0], [400, 0], [400, 400], [0, 400]], dtype=np.float32)
        result = self.corrector.correct(img, corners)
        assert result.shape == (400, 400, 3)
        # Values should be close to original
        assert np.mean(np.abs(result.astype(int) - 128)) < 5


class TestGridExtractor:
    """Tests for grid extraction."""

    def setup_method(self):
        self.extractor = GridExtractor()

    def test_extract_returns_8x8(self):
        """Should return exactly 64 squares in 8x8 grid."""
        warped = np.random.randint(0, 255, (400, 400, 3), dtype=np.uint8)
        grid = self.extractor.extract(warped)
        assert len(grid) == 8
        assert all(len(row) == 8 for row in grid)

    def test_each_square_is_50x50(self):
        """Each extracted square should be resized to 50x50."""
        warped = np.random.randint(0, 255, (400, 400, 3), dtype=np.uint8)
        grid = self.extractor.extract(warped)
        for row in grid:
            for square in row:
                assert square.shape == (50, 50, 3)

    def test_extract_with_coords(self):
        """Named extraction should label squares correctly."""
        warped = np.random.randint(0, 255, (400, 400, 3), dtype=np.uint8)
        squares = self.extractor.extract_with_coords(warped)
        assert len(squares) == 64
        assert squares[0]["square_name"] == "a8"
        assert squares[63]["square_name"] == "h1"
        assert squares[7]["square_name"] == "h8"


class TestPieceClassifier:
    """Tests for piece classification."""

    def setup_method(self):
        self.classifier = PieceClassifier()  # No model loaded — uses fallback

    def test_classify_returns_symbol_and_confidence(self):
        """Should return a tuple of (symbol, confidence)."""
        square = np.random.randint(100, 200, (50, 50, 3), dtype=np.uint8)
        symbol, conf = self.classifier.classify(square)
        assert isinstance(symbol, str)
        assert isinstance(conf, float)
        assert 0 <= conf <= 1

    def test_uniform_square_is_empty(self):
        """A uniformly colored square should classify as empty."""
        square = np.ones((50, 50, 3), dtype=np.uint8) * 150
        symbol, conf = self.classifier.classify(square)
        assert symbol == "."

    def test_classify_grid(self):
        """Grid classification should return 8x8 results."""
        grid = [[np.random.randint(0, 255, (50, 50, 3), dtype=np.uint8) for _ in range(8)] for _ in range(8)]
        results = self.classifier.classify_grid(grid)
        assert len(results) == 8
        assert all(len(row) == 8 for row in results)

    def test_all_classes_defined(self):
        """All 13 piece classes should be defined."""
        assert len(PIECE_CLASSES) == 13
        assert PIECE_CLASSES[0] == (".", "empty")
        assert PIECE_CLASSES[6] == ("K", "white_king")
        assert PIECE_CLASSES[12] == ("k", "black_king")


class TestFENGenerator:
    """Tests for FEN generation and validation."""

    def setup_method(self):
        self.gen = FENGenerator()

    def test_starting_position(self):
        """Starting position grid should generate correct FEN."""
        # Build starting position grid
        back_rank_w = [("R", 1), ("N", 1), ("B", 1), ("Q", 1), ("K", 1), ("B", 1), ("N", 1), ("R", 1)]
        pawn_rank_w = [("P", 1)] * 8
        empty_rank = [(".", 1)] * 8
        pawn_rank_b = [("p", 1)] * 8
        back_rank_b = [("r", 1), ("n", 1), ("b", 1), ("q", 1), ("k", 1), ("b", 1), ("n", 1), ("r", 1)]

        grid = [back_rank_b, pawn_rank_b, empty_rank, empty_rank, empty_rank, empty_rank, pawn_rank_w, back_rank_w]
        fen = self.gen.generate(grid)
        assert fen.startswith("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR")

    def test_validate_valid_fen(self):
        """Valid FEN should pass validation."""
        assert self.gen.validate("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1")

    def test_validate_invalid_fen(self):
        """Invalid FEN should fail validation."""
        assert not self.gen.validate("invalid fen string")

    def test_empty_board_fen(self):
        """All-empty grid should generate '8/8/8/8/8/8/8/8'."""
        grid = [[(".", 1)] * 8 for _ in range(8)]
        fen = self.gen.generate(grid)
        position_part = fen.split(" ")[0]
        assert position_part == "8/8/8/8/8/8/8/8"
