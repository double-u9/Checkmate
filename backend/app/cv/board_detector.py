"""Board detection using YOLOv8 or fallback Hough line detection."""

import cv2
import numpy as np
from pathlib import Path
from loguru import logger
from typing import Optional

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    logger.warning("Ultralytics not available, using fallback board detection")


class BoardDetector:
    """Detects a chessboard in an image using YOLO or OpenCV fallback."""

    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        if model_path and Path(model_path).exists() and YOLO_AVAILABLE:
            self.model = YOLO(model_path)
            logger.info(f"Loaded YOLO board detector: {model_path}")
        else:
            logger.info("Using OpenCV fallback board detection")

    def detect(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Detect the chessboard and return 4 corner points.

        Args:
            image: BGR image as numpy array

        Returns:
            4x2 numpy array of corner points (TL, TR, BR, BL) or None
        """
        if self.model:
            return self._detect_yolo(image)
        return self._detect_fallback(image)

    def _detect_yolo(self, image: np.ndarray) -> Optional[np.ndarray]:
        """Use YOLO to detect the board bounding box, then refine corners."""
        results = self.model(image, conf=0.5, verbose=False)

        if len(results) == 0 or len(results[0].boxes) == 0:
            logger.debug("YOLO: no board detected, falling back")
            return self._detect_fallback(image)

        # Get the highest confidence detection
        box = results[0].boxes[0]
        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)

        corners = np.array([
            [x1, y1],  # Top-left
            [x2, y1],  # Top-right
            [x2, y2],  # Bottom-right
            [x1, y2],  # Bottom-left
        ], dtype=np.float32)

        return corners

    def _detect_fallback(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Detect board using multiple fallback methods:
        1. 1D Edge Projection (perfect for axis-aligned digital screenshots).
        2. Traditional CV Contours (handles perspective but struggles with text).
        """
        h, w = image.shape[:2]

        # --- Method 1: 1D Edge Projection for Digital Screenshots ---
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        x_sum = np.sum(edges, axis=0)
        y_sum = np.sum(edges, axis=1)
        
        x_thresh = np.max(x_sum) * 0.3 if np.max(x_sum) > 0 else 1
        y_thresh = np.max(y_sum) * 0.3 if np.max(y_sum) > 0 else 1
        
        x_peaks_raw = np.where(x_sum > x_thresh)[0]
        y_peaks_raw = np.where(y_sum > y_thresh)[0]
        
        def group_peaks(peak_indices):
            peaks = []
            if len(peak_indices) == 0: return peaks
            current_peak = [peak_indices[0]]
            for i in range(1, len(peak_indices)):
                if peak_indices[i] - peak_indices[i-1] < 10:
                    current_peak.append(peak_indices[i])
                else:
                    peaks.append(int(np.mean(current_peak)))
                    current_peak = [peak_indices[i]]
            peaks.append(int(np.mean(current_peak)))
            return peaks
        
        def extrapolate_grid(peaks, max_dim):
            """From a set of edge peaks, find evenly-spaced grid lines and extrapolate to 9."""
            if len(peaks) < 3:
                return None
            spacings = [peaks[i+1] - peaks[i] for i in range(len(peaks)-1)]
            median_spacing = int(np.median(spacings))
            if median_spacing < 10:
                return None
            
            # Find the peak most consistent with the grid pattern
            best_base = peaks[0]
            best_score = 0
            for p in peaks:
                score = sum(1 for other in peaks if other != p 
                           and (abs(other - p) % median_spacing < 5 
                                or abs(other - p) % median_spacing > median_spacing - 5))
                if score > best_score:
                    best_score = score
                    best_base = p
            
            # Extrapolate backwards from base to find grid start
            steps_back = 0
            while best_base - (steps_back + 1) * median_spacing >= -2:
                steps_back += 1
            
            grid_start = best_base - steps_back * median_spacing
            grid = [max(0, grid_start + i * median_spacing) for i in range(9)]
            
            # Validate: the grid should span a significant portion of the image
            if grid[-1] - grid[0] < max_dim * 0.3:
                return None
            # Validate: aspect should be square-ish
            return grid

        xp = group_peaks(x_peaks_raw)
        yp = group_peaks(y_peaks_raw)
        
        x_grid = extrapolate_grid(xp, w)
        y_grid = extrapolate_grid(yp, h)
        
        if x_grid and y_grid:
            x1, x2 = x_grid[0], x_grid[8]
            y1, y2 = y_grid[0], y_grid[8]
            gw = x2 - x1
            gh = y2 - y1
            if gw > 50 and gh > 50:
                aspect = float(gw) / gh
                if 0.85 <= aspect <= 1.15:
                    logger.debug(f"Board detected via 1D Edge Projection: ({x1},{y1})-({x2},{y2})")
                    return np.array([
                        [x1, y1],
                        [x2, y1],
                        [x2, y2],
                        [x1, y2],
                    ], dtype=np.float32)

        # --- Method 2: Traditional CV Contours ---
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 2
        )
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            contours = sorted(contours, key=cv2.contourArea, reverse=True)
            for contour in contours[:5]:
                peri = cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, 0.02 * peri, True)

                if len(approx) == 4:
                    area = cv2.contourArea(approx)
                    img_area = image.shape[0] * image.shape[1]
                    if area > img_area * 0.05:
                        x, y, w_box, h_box = cv2.boundingRect(approx)
                        if 0.85 <= float(w_box)/h_box <= 1.15:
                            logger.debug("Board detected via Traditional Contours")
                            corners = self._order_corners(approx.reshape(4, 2))
                            return corners.astype(np.float32)

        # Last resort: use the whole image if it looks square-ish
        aspect = max(h, w) / min(h, w) if min(h, w) > 0 else 999
        if aspect < 1.3:
            margin = int(min(h, w) * 0.02)
            logger.debug("Board detected via Last Resort (Full Image)")
            return np.array([
                [margin, margin],
                [w - margin, margin],
                [w - margin, h - margin],
                [margin, h - margin],
            ], dtype=np.float32)

        return None

    @staticmethod
    def _order_corners(pts: np.ndarray) -> np.ndarray:
        """Order points as: top-left, top-right, bottom-right, bottom-left."""
        rect = np.zeros((4, 2), dtype=np.float32)
        s = pts.sum(axis=1)
        d = np.diff(pts, axis=1)

        rect[0] = pts[np.argmin(s)]   # Top-left has smallest sum
        rect[2] = pts[np.argmax(s)]   # Bottom-right has largest sum
        rect[1] = pts[np.argmin(d)]   # Top-right has smallest difference
        rect[3] = pts[np.argmax(d)]   # Bottom-left has largest difference

        return rect
