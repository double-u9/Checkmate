"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path


class Settings(BaseSettings):
    """Central configuration loaded from .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    debug: bool = True
    secret_key: str = "change-me-in-production"

    # Stockfish
    stockfish_path: str = str(Path(__file__).resolve().parent.parent / "stockfish" / "stockfish" / "stockfish-windows-x86-64-avx2.exe")
    stockfish_depth: int = 20
    stockfish_threads: int = 2
    stockfish_hash_mb: int = 256

    # Database (SQLite fallback for local dev without PostgreSQL)
    database_url: str = "sqlite+aiosqlite:///./aethelred.db"
    database_url_sync: str = "sqlite:///./aethelred.db"

    # CV Models
    cv_model_path: str = "ml/weights/board_detector.pt"
    piece_model_path: str = "ml/weights/piece_classifier.pth"
    cv_confidence_threshold: float = 0.5

    # Rate Limiting
    rate_limit_requests: int = 60
    rate_limit_window: int = 60

    # Paths
    base_dir: Path = Path(__file__).resolve().parent.parent


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings singleton."""
    return Settings()
