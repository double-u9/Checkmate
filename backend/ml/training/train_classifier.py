"""
Chess Piece Classifier Training Pipeline

Trains a ResNet18 CNN to classify chess pieces into 13 classes:
  empty, white_pawn, white_knight, white_bishop, white_rook, white_queen, white_king,
  black_pawn, black_knight, black_bishop, black_rook, black_queen, black_king

Usage:
    python train_classifier.py --data datasets/piece_classification --epochs 50
"""

import argparse
import os
import sys
import random
import shutil
from pathlib import Path

import numpy as np
from loguru import logger

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, Dataset
    from torchvision import models, transforms
    from PIL import Image
except ImportError:
    logger.error("PyTorch/torchvision not installed.")
    sys.exit(1)

try:
    import cv2
except ImportError:
    cv2 = None

# ─── Constants ────────────────────────────────────────────────────

CLASSES = [
    "empty",
    "white_pawn", "white_knight", "white_bishop",
    "white_rook", "white_queen", "white_king",
    "black_pawn", "black_knight", "black_bishop",
    "black_rook", "black_queen", "black_king",
]

FEN_TO_CLASS = {
    ".": 0,
    "P": 1, "N": 2, "B": 3, "R": 4, "Q": 5, "K": 6,
    "p": 7, "n": 8, "b": 9, "r": 10, "q": 11, "k": 12,
}

NUM_CLASSES = len(CLASSES)


# ─── Dataset ──────────────────────────────────────────────────────

class ChessPieceDataset(Dataset):
    """Dataset for chess piece square images."""

    def __init__(self, root_dir: str, transform=None):
        self.root_dir = Path(root_dir)
        self.transform = transform
        self.samples = []

        for class_idx, class_name in enumerate(CLASSES):
            class_dir = self.root_dir / class_name
            if class_dir.exists():
                for img_path in class_dir.glob("*"):
                    if img_path.suffix.lower() in (".png", ".jpg", ".jpeg", ".bmp"):
                        self.samples.append((str(img_path), class_idx))

        random.shuffle(self.samples)
        logger.info(f"Loaded {len(self.samples)} samples from {root_dir}")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_path, label = self.samples[idx]
        image = Image.open(img_path).convert("RGB")

        if self.transform:
            image = self.transform(image)

        return image, label


# ─── Synthetic Data Generator ────────────────────────────────────

PIECE_UNICODE = {
    "white_pawn": "♙", "white_knight": "♘", "white_bishop": "♗",
    "white_rook": "♖", "white_queen": "♕", "white_king": "♔",
    "black_pawn": "♟", "black_knight": "♞", "black_bishop": "♝",
    "black_rook": "♜", "black_queen": "♛", "black_king": "♚",
}


def generate_synthetic_pieces(output_dir: str, samples_per_class: int = 500):
    """
    Generate synthetic piece images by rendering pieces on colored squares.
    Uses PIL to draw Unicode chess symbols on light/dark square backgrounds.
    """
    from PIL import ImageDraw, ImageFont

    output_path = Path(output_dir)
    logger.info(f"Generating synthetic piece dataset ({samples_per_class}/class)...")

    # Try to load a font that supports chess unicode
    font = None
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/seguisym.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for fp in font_paths:
        try:
            font = ImageFont.truetype(fp, 36)
            break
        except (OSError, IOError):
            continue

    if font is None:
        font = ImageFont.load_default()

    # Color palettes for square backgrounds
    light_squares = [
        (240, 217, 181), (238, 238, 210), (222, 227, 230),
        (255, 255, 220), (230, 220, 200), (245, 245, 230),
    ]
    dark_squares = [
        (181, 136, 99), (118, 150, 86), (140, 162, 173),
        (170, 162, 58), (139, 105, 78), (100, 120, 100),
    ]

    for class_name in CLASSES:
        class_dir = output_path / class_name
        class_dir.mkdir(parents=True, exist_ok=True)

        for i in range(samples_per_class):
            # Random square color
            is_light = random.random() > 0.5
            bg_color = random.choice(light_squares if is_light else dark_squares)

            # Add slight noise
            bg_color = tuple(max(0, min(255, c + random.randint(-10, 10))) for c in bg_color)

            # Create image
            img_size = 64
            img = Image.new("RGB", (img_size, img_size), bg_color)
            draw = ImageDraw.Draw(img)

            if class_name != "empty":
                symbol = PIECE_UNICODE.get(class_name, "?")
                # Center the piece
                try:
                    bbox = draw.textbbox((0, 0), symbol, font=font)
                    tw = bbox[2] - bbox[0]
                    th = bbox[3] - bbox[1]
                except AttributeError:
                    tw, th = draw.textsize(symbol, font=font)

                x = (img_size - tw) // 2 + random.randint(-3, 3)
                y = (img_size - th) // 2 + random.randint(-3, 3)

                # Piece color
                if class_name.startswith("white"):
                    piece_color = (
                        255 + random.randint(-15, 0),
                        255 + random.randint(-15, 0),
                        255 + random.randint(-15, 0),
                    )
                else:
                    piece_color = (
                        random.randint(0, 30),
                        random.randint(0, 30),
                        random.randint(0, 30),
                    )

                draw.text((x, y), symbol, fill=piece_color, font=font)

            # Random augmentations
            if random.random() > 0.5:
                from PIL import ImageFilter
                img = img.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.3, 1.0)))

            if random.random() > 0.7:
                from PIL import ImageEnhance
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(random.uniform(0.7, 1.3))

            img.save(class_dir / f"{class_name}_{i:05d}.png")

        logger.info(f"  {class_name}: {samples_per_class} images")

    # Split into train/val
    _split_classification_dataset(output_dir, train_ratio=0.8)
    logger.info(f"Piece classification dataset generated at {output_dir}")


def _split_classification_dataset(dataset_dir: str, train_ratio: float = 0.8):
    """Split dataset into train and val directories."""
    dataset_path = Path(dataset_dir)
    train_dir = dataset_path / "train"
    val_dir = dataset_path / "val"

    for class_name in CLASSES:
        class_dir = dataset_path / class_name
        if not class_dir.exists():
            continue

        images = list(class_dir.glob("*"))
        random.shuffle(images)
        split_idx = int(len(images) * train_ratio)

        train_class = train_dir / class_name
        val_class = val_dir / class_name
        train_class.mkdir(parents=True, exist_ok=True)
        val_class.mkdir(parents=True, exist_ok=True)

        for img in images[:split_idx]:
            shutil.copy2(img, train_class / img.name)
        for img in images[split_idx:]:
            shutil.copy2(img, val_class / img.name)


# ─── Model ────────────────────────────────────────────────────────

def create_model(num_classes: int = NUM_CLASSES, pretrained: bool = True) -> nn.Module:
    """Create a ResNet18 model for piece classification."""
    weights = "IMAGENET1K_V1" if pretrained else None
    model = models.resnet18(weights=weights)

    # Replace final FC layer
    model.fc = nn.Sequential(
        nn.Dropout(0.3),
        nn.Linear(model.fc.in_features, num_classes),
    )

    return model


# ─── Training Loop ────────────────────────────────────────────────

def train(args):
    """Train the piece classifier."""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Training on: {device}")

    dataset_dir = args.data

    # Generate synthetic data if needed
    train_dir = Path(dataset_dir) / "train"
    if not train_dir.exists():
        logger.info("No dataset found. Generating synthetic training data...")
        generate_synthetic_pieces(dataset_dir, samples_per_class=args.samples_per_class)

    # Data transforms
    train_transform = transforms.Compose([
        transforms.Resize((64, 64)),
        transforms.RandomHorizontalFlip(p=0.3),
        transforms.RandomRotation(5),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.1),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    val_transform = transforms.Compose([
        transforms.Resize((64, 64)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    # Datasets
    train_dataset = ChessPieceDataset(str(train_dir), transform=train_transform)
    val_dir = Path(dataset_dir) / "val"
    val_dataset = ChessPieceDataset(str(val_dir), transform=val_transform) if val_dir.exists() else None

    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False, num_workers=2) if val_dataset else None

    # Model
    model = create_model(NUM_CLASSES, pretrained=True).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    best_val_acc = 0.0
    patience_counter = 0

    for epoch in range(args.epochs):
        # Training
        model.train()
        total_loss = 0
        correct = 0
        total = 0

        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)

            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            _, predicted = torch.max(outputs, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

        train_acc = 100 * correct / total
        avg_loss = total_loss / len(train_loader)

        # Validation
        val_acc = 0.0
        if val_loader:
            model.eval()
            val_correct = 0
            val_total = 0

            with torch.no_grad():
                for images, labels in val_loader:
                    images, labels = images.to(device), labels.to(device)
                    outputs = model(images)
                    _, predicted = torch.max(outputs, 1)
                    val_total += labels.size(0)
                    val_correct += (predicted == labels).sum().item()

            val_acc = 100 * val_correct / val_total

        scheduler.step()

        logger.info(
            f"Epoch {epoch + 1}/{args.epochs} | "
            f"Loss: {avg_loss:.4f} | Train Acc: {train_acc:.1f}% | Val Acc: {val_acc:.1f}%"
        )

        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            patience_counter = 0
            output_path = Path("weights") / "piece_classifier.pth"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            torch.save(model.state_dict(), output_path)
            logger.info(f"  ✅ Best model saved ({val_acc:.1f}%)")
        else:
            patience_counter += 1
            if patience_counter >= args.patience:
                logger.info(f"Early stopping at epoch {epoch + 1}")
                break

    logger.info(f"Training complete. Best validation accuracy: {best_val_acc:.1f}%")


# ─── CLI ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Train chess piece classifier")
    parser.add_argument("--data", type=str, default="datasets/piece_classification")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=0.001)
    parser.add_argument("--patience", type=int, default=10)
    parser.add_argument("--samples-per-class", type=int, default=500)

    args = parser.parse_args()
    train(args)


if __name__ == "__main__":
    main()
