"""
YOLO Board Detection Training Pipeline

Trains a YOLOv8 model to detect chessboards in images.
The model learns to identify the chessboard region and its four corners.

Usage:
    python train_yolo.py --data datasets/board_detection --epochs 100
"""

import argparse
import os
import sys
import shutil
import random
from pathlib import Path
from loguru import logger

try:
    from ultralytics import YOLO
except ImportError:
    logger.error("ultralytics not installed. Run: pip install ultralytics")
    sys.exit(1)

# ─── Configuration ────────────────────────────────────────────────

DEFAULT_CONFIG = {
    "model": "yolov8n.pt",          # Nano model for fast inference
    "epochs": 100,
    "imgsz": 640,
    "batch": 16,
    "patience": 15,
    "lr0": 0.01,
    "lrf": 0.001,
    "augment": True,
    "project": "runs/board_detect",
    "name": "train",
}


# ─── Synthetic Data Generator ────────────────────────────────────

def generate_synthetic_dataset(output_dir: str, num_images: int = 500):
    """
    Generate synthetic training data by rendering chessboards with
    python-chess SVG and converting to images with random backgrounds
    and perspective transforms.
    """
    import chess
    import chess.svg
    import numpy as np

    try:
        import cv2
        from PIL import Image
        import io
        import cairosvg
        HAS_CAIRO = True
    except ImportError:
        HAS_CAIRO = False
        logger.warning("cairosvg not available, using basic synthetic generation")

    images_dir = Path(output_dir) / "images"
    labels_dir = Path(output_dir) / "labels"
    images_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Generating {num_images} synthetic board images...")

    for i in range(num_images):
        # Create a random board position
        board = chess.Board()
        num_random_moves = random.randint(0, 40)
        for _ in range(num_random_moves):
            legal = list(board.legal_moves)
            if not legal:
                break
            board.push(random.choice(legal))

        # Generate image dimensions
        img_w, img_h = 640, 640

        if HAS_CAIRO:
            # Render SVG to PNG
            svg_data = chess.svg.board(board, size=400)
            png_data = cairosvg.svg2png(bytestring=svg_data.encode(), output_width=400, output_height=400)
            board_img = np.array(Image.open(io.BytesIO(png_data)).convert("RGB"))
            board_img = cv2.cvtColor(board_img, cv2.COLOR_RGB2BGR)
        else:
            # Simple colored grid as fallback
            import numpy as np
            board_img = np.zeros((400, 400, 3), dtype=np.uint8)
            sq_size = 50
            for r in range(8):
                for c in range(8):
                    color = (200, 180, 140) if (r + c) % 2 == 0 else (100, 70, 40)
                    y1, y2 = r * sq_size, (r + 1) * sq_size
                    x1, x2 = c * sq_size, (c + 1) * sq_size
                    board_img[y1:y2, x1:x2] = color

        # Place board on a random background
        bg = np.random.randint(20, 80, (img_h, img_w, 3), dtype=np.uint8)

        # Random position and scale
        scale = random.uniform(0.4, 0.85)
        board_size = int(400 * scale)

        try:
            board_resized = cv2.resize(board_img, (board_size, board_size))
        except Exception:
            board_resized = board_img[:board_size, :board_size]

        x_offset = random.randint(0, max(0, img_w - board_size))
        y_offset = random.randint(0, max(0, img_h - board_size))

        # Paste board onto background
        y_end = min(y_offset + board_size, img_h)
        x_end = min(x_offset + board_size, img_w)
        paste_h = y_end - y_offset
        paste_w = x_end - x_offset
        bg[y_offset:y_end, x_offset:x_end] = board_resized[:paste_h, :paste_w]

        # Save image
        img_path = images_dir / f"board_{i:05d}.jpg"
        cv2.imwrite(str(img_path), bg)

        # YOLO label: class x_center y_center width height (normalized)
        x_center = (x_offset + board_size / 2) / img_w
        y_center = (y_offset + board_size / 2) / img_h
        w_norm = board_size / img_w
        h_norm = board_size / img_h

        label_path = labels_dir / f"board_{i:05d}.txt"
        with open(label_path, "w") as f:
            f.write(f"0 {x_center:.6f} {y_center:.6f} {w_norm:.6f} {h_norm:.6f}\n")

        if (i + 1) % 100 == 0:
            logger.info(f"Generated {i + 1}/{num_images} images")

    # Split into train/val
    _split_dataset(output_dir, train_ratio=0.8)
    logger.info(f"Dataset generated at {output_dir}")


def _split_dataset(dataset_dir: str, train_ratio: float = 0.8):
    """Split images into train and val sets."""
    images_dir = Path(dataset_dir) / "images"
    labels_dir = Path(dataset_dir) / "labels"

    all_images = sorted(images_dir.glob("*.jpg"))
    random.shuffle(all_images)

    split_idx = int(len(all_images) * train_ratio)
    train_images = all_images[:split_idx]
    val_images = all_images[split_idx:]

    for split_name, split_images in [("train", train_images), ("val", val_images)]:
        split_img_dir = Path(dataset_dir) / split_name / "images"
        split_lbl_dir = Path(dataset_dir) / split_name / "labels"
        split_img_dir.mkdir(parents=True, exist_ok=True)
        split_lbl_dir.mkdir(parents=True, exist_ok=True)

        for img_path in split_images:
            shutil.copy2(img_path, split_img_dir / img_path.name)
            lbl_path = labels_dir / img_path.with_suffix(".txt").name
            if lbl_path.exists():
                shutil.copy2(lbl_path, split_lbl_dir / lbl_path.name)

    logger.info(f"Split: {len(train_images)} train, {len(val_images)} val")


def create_data_yaml(dataset_dir: str) -> str:
    """Create the YOLO data.yaml configuration file."""
    yaml_content = f"""# Aethelred Board Detection Dataset
path: {os.path.abspath(dataset_dir)}
train: train/images
val: val/images

nc: 1
names:
  0: chessboard
"""
    yaml_path = os.path.join(dataset_dir, "data.yaml")
    with open(yaml_path, "w") as f:
        f.write(yaml_content)

    logger.info(f"Created data.yaml at {yaml_path}")
    return yaml_path


# ─── Training ─────────────────────────────────────────────────────

def train(args):
    """Train the YOLO board detection model."""
    dataset_dir = args.data

    # Generate synthetic data if dataset doesn't exist
    if not Path(dataset_dir).exists() or not any(Path(dataset_dir).iterdir()):
        logger.info("No dataset found. Generating synthetic training data...")
        generate_synthetic_dataset(dataset_dir, num_images=args.num_synthetic)

    # Create data.yaml
    data_yaml = create_data_yaml(dataset_dir)

    # Load pretrained model
    model = YOLO(args.model)
    logger.info(f"Loaded base model: {args.model}")

    # Train
    results = model.train(
        data=data_yaml,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        patience=args.patience,
        lr0=args.lr0,
        lrf=args.lrf,
        augment=args.augment,
        project=args.project,
        name=args.name,
        exist_ok=True,
        verbose=True,
    )

    # Export best model
    best_path = Path(args.project) / args.name / "weights" / "best.pt"
    output_path = Path("weights") / "board_detector.pt"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if best_path.exists():
        shutil.copy2(best_path, output_path)
        logger.info(f"Best model saved to {output_path}")
    else:
        logger.warning("Training completed but best.pt not found")

    return results


# ─── CLI ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Train YOLO board detector for Aethelred")
    parser.add_argument("--data", type=str, default="datasets/board_detection", help="Dataset directory")
    parser.add_argument("--model", type=str, default=DEFAULT_CONFIG["model"], help="Base YOLO model")
    parser.add_argument("--epochs", type=int, default=DEFAULT_CONFIG["epochs"])
    parser.add_argument("--imgsz", type=int, default=DEFAULT_CONFIG["imgsz"])
    parser.add_argument("--batch", type=int, default=DEFAULT_CONFIG["batch"])
    parser.add_argument("--patience", type=int, default=DEFAULT_CONFIG["patience"])
    parser.add_argument("--lr0", type=float, default=DEFAULT_CONFIG["lr0"])
    parser.add_argument("--lrf", type=float, default=DEFAULT_CONFIG["lrf"])
    parser.add_argument("--augment", action="store_true", default=DEFAULT_CONFIG["augment"])
    parser.add_argument("--project", type=str, default=DEFAULT_CONFIG["project"])
    parser.add_argument("--name", type=str, default=DEFAULT_CONFIG["name"])
    parser.add_argument("--num-synthetic", type=int, default=500, help="Number of synthetic images to generate")

    args = parser.parse_args()
    train(args)


if __name__ == "__main__":
    main()
