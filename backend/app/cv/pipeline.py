"""CV Pipeline — orchestrates the full board detection → FEN pipeline."""

import cv2
import asyncio
import numpy as np
from loguru import logger

from app.config import get_settings
from app.cv.board_detector import BoardDetector
from app.cv.perspective import PerspectiveCorrector
from app.cv.grid_extractor import GridExtractor
from app.cv.piece_classifier import PieceClassifier
from app.cv.fen_generator import FENGenerator


class CVPipeline:
    """
    Full computer vision pipeline:
    Image → Board Detection → Perspective Correction → Grid Extraction →
    Piece Classification → FEN Generation
    """

    def __init__(self):
        settings = get_settings()
        self.detector = BoardDetector(model_path=settings.cv_model_path)
        self.corrector = PerspectiveCorrector()
        self.extractor = GridExtractor()
        self.classifier = PieceClassifier(model_path=settings.piece_model_path)
        self.fen_gen = FENGenerator()
        logger.info("CV Pipeline initialized")

    async def process_image(self, image_data: np.ndarray) -> dict:
        """
        Process an image through the full pipeline.

        Args:
            image_data: Raw image bytes as numpy array (from np.frombuffer)

        Returns:
            Dict with keys: fen, confidence, board_detected, squares
        """
        # Run CPU-bound operations in thread pool
        return await asyncio.to_thread(self._process_sync, image_data)

    def _process_sync(self, image_data: np.ndarray) -> dict:
        """Synchronous pipeline execution."""
        # Decode image
        image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
        if image is None:
            return {
                "fen": "",
                "confidence": 0.0,
                "board_detected": False,
                "squares": None,
            }

        # Step 1: Detect board corners
        corners = self.detector.detect(image)
        if corners is None:
            logger.debug("No board detected in image")
            return {
                "fen": "",
                "confidence": 0.0,
                "board_detected": False,
                "squares": None,
            }

        # Step 2: Perspective correction
        warped = self.corrector.correct(image, corners)

        # Step 3: Grid extraction
        grid = self.extractor.extract(warped)

        # Step 4: Piece classification
        classifications = self.classifier.classify_grid(grid)

        # Step 5: Generate FEN
        fen = self.fen_gen.generate(classifications)

        # Calculate overall confidence
        confidences = [conf for row in classifications for _, conf in row]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        # Build squares info for the frontend
        files = "abcdefgh"
        squares = []
        for row in range(8):
            for col in range(8):
                symbol, conf = classifications[row][col]
                if symbol != ".":
                    squares.append({
                        "square": f"{files[col]}{8 - row}",
                        "piece": symbol,
                        "confidence": round(conf, 3),
                    })

        return {
            "fen": fen,
            "confidence": round(avg_confidence, 3),
            "board_detected": True,
            "squares": squares,
        }

    def process_fen_direct(self, fen: str) -> dict:
        """
        Bypass CV and accept a FEN string directly.
        Used for manual input or when FEN is already known.
        """
        valid = self.fen_gen.validate(fen)
        return {
            "fen": fen,
            "confidence": 1.0 if valid else 0.0,
            "board_detected": valid,
            "squares": None,
        }
