"""Grid extraction — divides a warped board into 64 individual squares."""

import cv2
import numpy as np
from loguru import logger


class GridExtractor:
    """Splits a rectified chessboard image into 64 individual square images."""

    def extract(self, warped_board: np.ndarray) -> list[list[np.ndarray]]:
        """
        Divide the warped board into an 8x8 grid of square images.

        Args:
            warped_board: Rectified square board image (400x400)

        Returns:
            8x8 list of square images. grid[row][col] where
            row 0 = rank 8 (top), col 0 = file a (left)
        """
        h, w = warped_board.shape[:2]
        sq_h = h // 8
        sq_w = w // 8

        grid = []
        for row in range(8):
            row_squares = []
            for col in range(8):
                y1 = row * sq_h
                y2 = (row + 1) * sq_h
                x1 = col * sq_w
                x2 = (col + 1) * sq_w

                square = warped_board[y1:y2, x1:x2].copy()
                # Resize to standard 50x50 for classifier
                square = cv2.resize(square, (50, 50))
                row_squares.append(square)
            grid.append(row_squares)

        logger.debug(f"Extracted 8x8 grid ({sq_w}x{sq_h} per square)")
        return grid

    def extract_with_coords(self, warped_board: np.ndarray) -> list[dict]:
        """
        Extract squares with chess coordinate labels.

        Returns:
            List of 64 dicts: {image, file, rank, square_name}
        """
        grid = self.extract(warped_board)
        squares = []
        files = "abcdefgh"

        for row in range(8):
            for col in range(8):
                squares.append({
                    "image": grid[row][col],
                    "file": files[col],
                    "rank": 8 - row,
                    "square_name": f"{files[col]}{8 - row}",
                })

        return squares
