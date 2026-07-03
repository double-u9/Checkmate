"""SQLAlchemy database models."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base


def generate_uuid():
    return str(uuid.uuid4())


def _utcnow():
    """Return timezone-aware UTC timestamp (replaces deprecated datetime.utcnow)."""
    return datetime.now(timezone.utc)


class Game(Base):
    """A chess game with full move history."""

    __tablename__ = "games"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    white_name = Column(String(255), default="Unknown")
    black_name = Column(String(255), default="Unknown")
    result = Column(String(10), nullable=True)  # 1-0, 0-1, 1/2-1/2, *
    pgn = Column(Text, nullable=True)
    opening_eco = Column(String(10), nullable=True)
    opening_name = Column(String(255), nullable=True)
    source = Column(String(50), default="upload")  # upload, webcam, manual, import
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    # Relationships
    positions = relationship("Position", back_populates="game", cascade="all, delete-orphan")


class Position(Base):
    """A single position within a game, with analysis."""

    __tablename__ = "positions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    game_id = Column(String(36), ForeignKey("games.id"), nullable=False)
    move_number = Column(Integer, nullable=False)
    fen = Column(String(100), nullable=False)
    move_uci = Column(String(10), nullable=True)
    move_san = Column(String(10), nullable=True)
    evaluation = Column(Float, nullable=True)
    best_move = Column(String(10), nullable=True)
    explanation = Column(Text, nullable=True)
    threats = Column(JSON, nullable=True)
    classification = Column(String(50), nullable=True)  # blunder, mistake, inaccuracy, good, excellent, brilliant
    heatmap = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    # Relationships
    game = relationship("Game", back_populates="positions")


class Profile(Base):
    """Opponent psychological and strategic profile."""

    __tablename__ = "profiles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    player_name = Column(String(255), unique=True, nullable=False)
    style = Column(String(50), nullable=True)  # attacker, positional, universal, defender
    aggression_score = Column(Float, default=0.5)
    risk_tolerance = Column(Float, default=0.5)
    tactical_preference = Column(Float, default=0.5)
    positional_preference = Column(Float, default=0.5)
    endgame_skill = Column(Float, default=0.5)
    opening_stats = Column(JSON, nullable=True)
    psychological_profile = Column(JSON, nullable=True)
    total_games_analyzed = Column(Integer, default=0)
    avg_centipawn_loss = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)
