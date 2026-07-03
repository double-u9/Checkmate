"""Pytest configuration."""

import sys
from pathlib import Path

# Add backend app to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
