"""Piece classifier using a CNN (ResNet18) or color-histogram fallback."""

import cv2
import numpy as np
from pathlib import Path
from typing import Optional
from loguru import logger

try:
    import torch
    import torch.nn as nn
    from torchvision import models, transforms
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available, using fallback piece classifier")


# Piece labels: index → (symbol, name)
PIECE_CLASSES = {
    0: (".", "empty"),
    1: ("P", "white_pawn"),
    2: ("N", "white_knight"),
    3: ("B", "white_bishop"),
    4: ("R", "white_rook"),
    5: ("Q", "white_queen"),
    6: ("K", "white_king"),
    7: ("p", "black_pawn"),
    8: ("n", "black_knight"),
    9: ("b", "black_bishop"),
    10: ("r", "black_rook"),
    11: ("q", "black_queen"),
    12: ("k", "black_king"),
}

NUM_CLASSES = len(PIECE_CLASSES)


class PieceClassifier:
    """Classifies chess pieces from individual square images."""

    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.transform = None
        self.device = "cpu"
        
        # Load templates for fallback — pre-composite onto both light and dark backgrounds
        self.composited_templates = {}  # {p_code: [(composited_on_light_50, composited_on_dark_50), ...]}
        self.raw_templates = {}  # {p_code: (bgr_50, alpha_50)}
        base_dir = Path(__file__).resolve().parent.parent.parent
        template_dir = base_dir / "ml" / "templates"
        
        # Chess.com style backgrounds (BGR)
        bg_light = np.array([210, 238, 238], dtype=np.uint8)  # beige/cream
        bg_dark = np.array([86, 150, 118], dtype=np.uint8)    # green
        
        if template_dir.exists():
            for p in ["wp", "wn", "wb", "wr", "wq", "wk", "bp", "bn", "bb", "br", "bq", "bk"]:
                t_path = template_dir / f"{p}.png"
                if t_path.exists():
                    img = cv2.imread(str(t_path), cv2.IMREAD_UNCHANGED)
                    if img is not None and img.shape[2] == 4:
                        # Resize to 50x50
                        resized = cv2.resize(img, (50, 50), interpolation=cv2.INTER_AREA)
                        bgr = resized[:, :, :3]
                        alpha = resized[:, :, 3]
                        self.raw_templates[p] = (bgr, alpha)
                        
                        # Composite onto light and dark backgrounds
                        alpha_f = alpha.astype(np.float32) / 255.0
                        alpha_3 = np.stack([alpha_f]*3, axis=-1)
                        bgr_f = bgr.astype(np.float32)
                        
                        comp_light = (alpha_3 * bgr_f + (1 - alpha_3) * bg_light.astype(np.float32)).astype(np.uint8)
                        comp_dark = (alpha_3 * bgr_f + (1 - alpha_3) * bg_dark.astype(np.float32)).astype(np.uint8)
                        
                        self.composited_templates[p] = (comp_light, comp_dark)
            
            # Also create "empty" composited templates (just the backgrounds)
            self._empty_light = np.full((50, 50, 3), bg_light, dtype=np.uint8)
            self._empty_dark = np.full((50, 50, 3), bg_dark, dtype=np.uint8)

        if TORCH_AVAILABLE:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self._init_model(model_path)

    def _init_model(self, model_path: Optional[str]):
        """Initialize the ResNet18 classifier."""
        model = models.resnet18(weights=None)
        model.fc = nn.Linear(model.fc.in_features, NUM_CLASSES)

        if model_path and Path(model_path).exists():
            state_dict = torch.load(model_path, map_location=self.device)
            model.load_state_dict(state_dict)
            logger.info(f"Loaded piece classifier: {model_path}")
        else:
            logger.info("Piece classifier: no weights loaded, using template matching fallback")

        model.to(self.device)
        model.eval()
        self.model = model

        self.transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((64, 64)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

    def classify(self, square_image: np.ndarray) -> tuple[str, float]:
        """
        Classify a single square image.

        Args:
            square_image: 50x50 BGR image of one square

        Returns:
            (piece_symbol, confidence) e.g. ("P", 0.95)
        """
        if self.model and TORCH_AVAILABLE:
            return self._classify_cnn(square_image)
        return self._classify_fallback(square_image)

    def _classify_cnn(self, square_image: np.ndarray) -> tuple[str, float]:
        """Use CNN for classification."""
        rgb = cv2.cvtColor(square_image, cv2.COLOR_BGR2RGB)
        tensor = self.transform(rgb).unsqueeze(0).to(self.device)

        with torch.no_grad():
            output = self.model(tensor)
            probs = torch.softmax(output, dim=1)
            confidence, predicted = torch.max(probs, 1)

        class_idx = predicted.item()
        conf = confidence.item()
        symbol = PIECE_CLASSES[class_idx][0]

        return symbol, conf

    def _classify_fallback(self, square_image: np.ndarray) -> tuple[str, float]:
        """
        Fallback classifier using composited template matching.
        Each template is pre-composited onto both light and dark Chess.com backgrounds,
        then the full 50x50 image is compared via MSE. This ensures white pieces on
        light squares are detected (their dark outlines create measurable contrast).
        """
        if not self.composited_templates:
            return self._classify_color(square_image)
            
        sq = cv2.resize(square_image, (50, 50)) if square_image.shape[:2] != (50, 50) else square_image
        sq_f = sq.astype(np.float32)
        
        # Determine if this is a light or dark square by average color
        avg_color = np.mean(sq_f, axis=(0, 1))
        is_light = np.mean(avg_color) > 160
        
        # Calculate MSE for empty square first
        empty_template = self._empty_light if is_light else self._empty_dark
        empty_mse = np.mean((sq_f - empty_template.astype(np.float32)) ** 2)
        
        best_mse = float('inf')
        best_piece = "."
        
        code_to_symbol = {
            'wp': 'P', 'wn': 'N', 'wb': 'B', 'wr': 'R', 'wq': 'Q', 'wk': 'K',
            'bp': 'p', 'bn': 'n', 'bb': 'b', 'br': 'r', 'bq': 'q', 'bk': 'k'
        }

        for p_code, (comp_light, comp_dark) in self.composited_templates.items():
            template = comp_light if is_light else comp_dark
            t_f = template.astype(np.float32)
            
            # Try sliding the template by a few pixels for alignment tolerance
            min_piece_mse = float('inf')
            for dy in range(-3, 4, 2):
                for dx in range(-3, 4, 2):
                    # Shift the template
                    M = np.float32([[1, 0, dx], [0, 1, dy]])
                    shifted = cv2.warpAffine(t_f, M, (50, 50), borderMode=cv2.BORDER_REPLICATE)
                    
                    mse = np.mean((sq_f - shifted) ** 2)
                    if mse < min_piece_mse:
                        min_piece_mse = mse
            
            if min_piece_mse < best_mse:
                best_mse = min_piece_mse
                best_piece = p_code

        # Compare: is the best piece match better than empty square?
        # A piece should have significantly lower MSE than empty
        if best_mse < empty_mse * 0.85:
            conf = max(0.0, min(1.0, 1.0 - (best_mse / empty_mse)))
            return code_to_symbol.get(best_piece, "."), float(conf)
        
        return ".", 1.0
    
    def _classify_color(self, square_image: np.ndarray) -> tuple[str, float]:
        """Ultra-basic color fallback if no templates are available."""
        gray = cv2.cvtColor(square_image, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        margin = int(min(h, w) * 0.2)
        center = gray[margin:h - margin, margin:w - margin]
        mean_val = np.mean(center)
        std_val = np.std(center)
        if std_val < 15:
            return ".", 0.7
        if std_val > 30:
            if mean_val > 140:
                return "P", 0.3
            else:
                return "p", 0.3
        return ".", 0.5

    def classify_grid(self, grid: list[list[np.ndarray]]) -> list[list[tuple[str, float]]]:
        """
        Classify all 64 squares in a grid.

        Args:
            grid: 8x8 list of square images

        Returns:
            8x8 list of (piece_symbol, confidence) tuples
        """
        results = []
        for row in grid:
            row_results = []
            for square in row:
                symbol, conf = self.classify(square)
                row_results.append((symbol, conf))
            results.append(row_results)
        return results
