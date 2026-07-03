# Chess Piece Datasets

## Recommended Datasets

1. **Chess Pieces Dataset (Kaggle)**
   - URL: https://www.kaggle.com/datasets/niteshfre/chessman-image-dataset
   - 13 classes (6 white + 6 black + empty)

2. **Roboflow Chess Board Detection**
   - URL: https://universe.roboflow.com/chess-detection
   - YOLO-compatible annotations

3. **Synthetic Generation**
   - Use `python-chess` SVG rendering to create training data
   - Render pieces on various board themes
   - Apply augmentations (rotation, lighting, blur)

## Directory Structure After Download

```
datasets/
├── board_detection/
│   ├── images/
│   └── labels/
├── piece_classification/
│   ├── train/
│   │   ├── empty/
│   │   ├── white_pawn/
│   │   ├── white_knight/
│   │   └── ...
│   └── val/
└── profiler/
    └── pgn_games/
```
