"""Perspective transformation to rectify a chessboard to a perfect square."""

import cv2
import numpy as np
from loguru import logger


class PerspectiveCorrector:
    """Warps a detected chessboard region into a perfect top-down square."""

    OUTPUT_SIZE = 400  # Output square size in pixels

    def correct(self, image: np.ndarray, corners: np.ndarray) -> np.ndarray:
        """
        Apply perspective transformation.

        Args:
            image: Original BGR image
            corners: 4x2 array of corner points (TL, TR, BR, BL)

        Returns:
            Warped 400x400 BGR image of the board
        """
        dst_points = np.array([
            [0, 0],
            [self.OUTPUT_SIZE, 0],
            [self.OUTPUT_SIZE, self.OUTPUT_SIZE],
            [0, self.OUTPUT_SIZE],
        ], dtype=np.float32)

        matrix = cv2.getPerspectiveTransform(corners.astype(np.float32), dst_points)
        warped = cv2.warpPerspective(image, matrix, (self.OUTPUT_SIZE, self.OUTPUT_SIZE))

        logger.debug(f"Perspective corrected to {self.OUTPUT_SIZE}x{self.OUTPUT_SIZE}")
        return warped
