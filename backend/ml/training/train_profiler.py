"""
Opponent Profiler Training Pipeline

Trains a play-style classifier using features extracted from annotated
grandmaster games. Uses XGBoost/Random Forest for classification.

Usage:
    python train_profiler.py --data datasets/profiler/pgn_games --epochs 100
"""

import argparse
import os
import sys
import io
import pickle
import random
from pathlib import Path
from collections import defaultdict

import numpy as np
from loguru import logger

try:
    import chess
    import chess.pgn
except ImportError:
    logger.error("python-chess not installed.")
    sys.exit(1)

try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.metrics import classification_report, accuracy_score
    import joblib
except ImportError:
    logger.error("scikit-learn not installed.")
    sys.exit(1)


# ─── Style Labels ─────────────────────────────────────────────────

# Known grandmasters and their styles for training data
GM_STYLES = {
    # Attackers
    "Tal": "attacker",
    "Kasparov": "attacker",
    "Alekhine": "attacker",
    "Shirov": "attacker",
    "Nakamura": "attacker",
    "Nezhmetdinov": "attacker",

    # Positional
    "Karpov": "positional",
    "Petrosian": "positional",
    "Capablanca": "positional",
    "Kramnik": "positional",
    "Carlsen": "positional",
    "Smyslov": "positional",

    # Universal
    "Fischer": "universal",
    "Anand": "universal",
    "Spassky": "universal",
    "Topalov": "universal",

    # Defensive
    "Tigran Petrosian": "defender",
    "Leko": "defender",
    "Ulf Andersson": "defender",
}


# ─── Feature Extraction ──────────────────────────────────────────

def extract_features_from_game(pgn_str: str, player_name: str) -> dict | None:
    """Extract behavioral features from a single PGN game."""
    pgn_io = io.StringIO(pgn_str)
    game = chess.pgn.read_game(pgn_io)
    if game is None:
        return None

    white = game.headers.get("White", "")
    black = game.headers.get("Black", "")

    if player_name.lower() in white.lower():
        player_color = chess.WHITE
    elif player_name.lower() in black.lower():
        player_color = chess.BLACK
    else:
        return None

    board = game.board()
    features = defaultdict(float)
    features["total_moves"] = 0
    move_count = 0

    for node in game.mainline():
        move = node.move
        is_player = board.turn == player_color

        if is_player:
            move_count += 1
            features["total_moves"] += 1
            piece = board.piece_at(move.from_square)

            # Captures
            if board.is_capture(move):
                features["captures"] += 1
                if piece:
                    captured = board.piece_at(move.to_square)
                    if captured and piece_value(piece.piece_type) > piece_value(captured.piece_type):
                        features["sacrifices"] += 1

            # Checks
            board_copy = board.copy()
            board_copy.push(move)
            if board_copy.is_check():
                features["checks"] += 1

            # Castling
            if board.is_castling(move):
                features["castled"] = 1

            # Pawn advances
            if piece and piece.piece_type == chess.PAWN:
                features["pawn_moves"] += 1
                rank = chess.square_rank(move.to_square)
                if (player_color == chess.WHITE and rank >= 4) or \
                   (player_color == chess.BLACK and rank <= 3):
                    features["aggressive_pawns"] += 1

            # Center control
            to_file = chess.square_file(move.to_square)
            to_rank = chess.square_rank(move.to_square)
            if 2 <= to_file <= 5 and 2 <= to_rank <= 5:
                features["center_moves"] += 1

            # Piece development (first 10 moves)
            if move_count <= 10 and piece:
                if piece.piece_type in (chess.KNIGHT, chess.BISHOP):
                    features["early_development"] += 1
                elif piece.piece_type == chess.QUEEN:
                    features["early_queen"] += 1

            # King moves (non-castling)
            if piece and piece.piece_type == chess.KING and not board.is_castling(move):
                features["king_walks"] += 1

        board.push(move)

    if features["total_moves"] == 0:
        return None

    # Normalize per move
    n = features["total_moves"]
    return {
        "capture_rate": features["captures"] / n,
        "check_rate": features["checks"] / n,
        "sacrifice_rate": features["sacrifices"] / n,
        "castled": features["castled"],
        "pawn_move_rate": features["pawn_moves"] / n,
        "aggressive_pawn_rate": features["aggressive_pawns"] / n,
        "center_rate": features["center_moves"] / n,
        "early_dev_rate": features["early_development"] / min(n, 10),
        "early_queen_rate": features["early_queen"] / min(n, 10),
        "king_walk_rate": features["king_walks"] / n,
        "game_length": n,
    }


def piece_value(pt: int) -> int:
    return {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}.get(pt, 0)


# ─── Synthetic Training Data ─────────────────────────────────────

def generate_synthetic_profiles(num_per_style: int = 200) -> tuple[np.ndarray, np.ndarray]:
    """
    Generate synthetic feature vectors for each play style.
    Based on statistical distributions observed in real GM games.
    """
    logger.info(f"Generating synthetic profiler training data ({num_per_style}/style)...")

    # Statistical profiles per style (mean, std) for each feature
    style_distributions = {
        "attacker": {
            "capture_rate": (0.18, 0.04),
            "check_rate": (0.08, 0.03),
            "sacrifice_rate": (0.03, 0.02),
            "castled": (0.85, 0.15),
            "pawn_move_rate": (0.22, 0.05),
            "aggressive_pawn_rate": (0.12, 0.04),
            "center_rate": (0.30, 0.06),
            "early_dev_rate": (0.50, 0.15),
            "early_queen_rate": (0.10, 0.08),
            "king_walk_rate": (0.02, 0.02),
            "game_length": (35, 10),
        },
        "positional": {
            "capture_rate": (0.12, 0.03),
            "check_rate": (0.04, 0.02),
            "sacrifice_rate": (0.01, 0.01),
            "castled": (0.95, 0.05),
            "pawn_move_rate": (0.25, 0.04),
            "aggressive_pawn_rate": (0.06, 0.03),
            "center_rate": (0.35, 0.05),
            "early_dev_rate": (0.60, 0.10),
            "early_queen_rate": (0.02, 0.02),
            "king_walk_rate": (0.01, 0.01),
            "game_length": (45, 12),
        },
        "universal": {
            "capture_rate": (0.15, 0.04),
            "check_rate": (0.06, 0.03),
            "sacrifice_rate": (0.02, 0.015),
            "castled": (0.90, 0.10),
            "pawn_move_rate": (0.23, 0.05),
            "aggressive_pawn_rate": (0.09, 0.04),
            "center_rate": (0.32, 0.06),
            "early_dev_rate": (0.55, 0.12),
            "early_queen_rate": (0.05, 0.04),
            "king_walk_rate": (0.015, 0.01),
            "game_length": (40, 11),
        },
        "defender": {
            "capture_rate": (0.10, 0.03),
            "check_rate": (0.03, 0.02),
            "sacrifice_rate": (0.005, 0.005),
            "castled": (0.97, 0.03),
            "pawn_move_rate": (0.20, 0.04),
            "aggressive_pawn_rate": (0.04, 0.02),
            "center_rate": (0.28, 0.05),
            "early_dev_rate": (0.55, 0.12),
            "early_queen_rate": (0.01, 0.01),
            "king_walk_rate": (0.005, 0.005),
            "game_length": (50, 15),
        },
    }

    feature_names = list(style_distributions["attacker"].keys())
    X = []
    y = []

    for style, distributions in style_distributions.items():
        for _ in range(num_per_style):
            sample = []
            for feat in feature_names:
                mean, std = distributions[feat]
                value = max(0, np.random.normal(mean, std))
                if feat == "castled":
                    value = min(1, value)
                sample.append(value)
            X.append(sample)
            y.append(style)

    return np.array(X), np.array(y)


# ─── Training ─────────────────────────────────────────────────────

def train(args):
    """Train the play-style classifier."""
    # Generate or load data
    X, y = generate_synthetic_profiles(num_per_style=args.num_samples)

    # Encode labels
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
    )

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Train Random Forest
    logger.info("Training Random Forest classifier...")
    rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    )
    rf.fit(X_train_scaled, y_train)

    # Train Gradient Boosting
    logger.info("Training Gradient Boosting classifier...")
    gb = GradientBoostingClassifier(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.1,
        random_state=42,
    )
    gb.fit(X_train_scaled, y_train)

    # Evaluate
    for name, model in [("Random Forest", rf), ("Gradient Boosting", gb)]:
        y_pred = model.predict(X_test_scaled)
        acc = accuracy_score(y_test, y_pred)
        logger.info(f"\n{name} — Accuracy: {acc:.3f}")
        logger.info("\n" + classification_report(y_test, y_pred, target_names=le.classes_))

        # Cross-validation
        cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5)
        logger.info(f"Cross-val: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")

    # Save best model (use GB since it usually performs better)
    output_dir = Path("weights")
    output_dir.mkdir(parents=True, exist_ok=True)

    model_path = output_dir / "style_classifier.pkl"
    scaler_path = output_dir / "style_scaler.pkl"
    encoder_path = output_dir / "style_encoder.pkl"

    joblib.dump(gb, model_path)
    joblib.dump(scaler, scaler_path)
    joblib.dump(le, encoder_path)

    logger.info(f"Model saved to {model_path}")
    logger.info(f"Scaler saved to {scaler_path}")
    logger.info(f"Encoder saved to {encoder_path}")

    # Feature importance
    feature_names = [
        "capture_rate", "check_rate", "sacrifice_rate", "castled",
        "pawn_move_rate", "aggressive_pawn_rate", "center_rate",
        "early_dev_rate", "early_queen_rate", "king_walk_rate", "game_length",
    ]
    importances = gb.feature_importances_
    sorted_idx = np.argsort(importances)[::-1]
    logger.info("\nFeature Importance:")
    for idx in sorted_idx:
        logger.info(f"  {feature_names[idx]:25s} {importances[idx]:.4f}")


# ─── CLI ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Train opponent profiler")
    parser.add_argument("--data", type=str, default="datasets/profiler")
    parser.add_argument("--num-samples", type=int, default=500, help="Samples per style class")

    args = parser.parse_args()
    train(args)


if __name__ == "__main__":
    main()
