"""Pydantic schemas for API request/response validation."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


# ─── Vision Schemas ───────────────────────────────────────────────

class BoardDetectionResponse(BaseModel):
    """Response from the CV board detection pipeline."""
    fen: str
    confidence: float
    board_detected: bool
    squares: Optional[list[dict]] = None
    processing_time_ms: float


class Base64ImageRequest(BaseModel):
    """Request containing a base64-encoded image."""
    image: str = Field(..., max_length=15_000_000, description="Base64-encoded image data (max ~10MB)")



# ─── Analysis Schemas ─────────────────────────────────────────────

class PositionAnalysisRequest(BaseModel):
    """Request to analyze a chess position."""
    fen: str
    depth: int = Field(default=20, ge=1, le=30)
    num_lines: int = Field(default=3, ge=1, le=5)


class MoveEvaluation(BaseModel):
    """Evaluation of a single move."""
    move_uci: str
    move_san: str
    score: float
    mate_in: Optional[int] = None
    is_best: bool = False
    classification: str = "good"  # blunder, mistake, inaccuracy, good, excellent, brilliant


class ThreatInfo(BaseModel):
    """Information about a tactical threat."""
    type: str  # fork, pin, skewer, discovered_attack, mate_threat, hanging_piece
    description: str
    severity: str  # low, medium, high, critical
    squares: list[str]


class AnalysisResponse(BaseModel):
    """Full analysis response for a position."""
    fen: str
    evaluation: float
    mate_in: Optional[int] = None
    best_move: MoveEvaluation
    top_lines: list[list[MoveEvaluation]]
    threats: list[ThreatInfo]
    explanation: str
    strategic_themes: list[str]
    position_type: str  # opening, middlegame, endgame
    heatmap: Optional[list[list[float]]] = None


class ExplanationRequest(BaseModel):
    """Request for a move explanation."""
    fen: str
    move_uci: str
    depth: int = Field(default=20, ge=1, le=30)


class ExplanationResponse(BaseModel):
    """Human-readable move explanation."""
    move_san: str
    evaluation_before: float
    evaluation_after: float
    explanation: str
    tactical_motifs: list[str]
    strategic_ideas: list[str]
    classification: str


# ─── Game Schemas ─────────────────────────────────────────────────

class GameCreate(BaseModel):
    """Create a new game."""
    white_name: str = "White"
    black_name: str = "Black"
    source: str = "manual"


class GameResponse(BaseModel):
    """Game information."""
    id: UUID
    white_name: str
    black_name: str
    result: Optional[str] = None
    pgn: Optional[str] = None
    opening_eco: Optional[str] = None
    opening_name: Optional[str] = None
    source: str
    created_at: datetime
    move_count: int = 0

    class Config:
        from_attributes = True


class AddMoveRequest(BaseModel):
    """Add a move to a game."""
    fen: str
    move_uci: Optional[str] = None
    move_san: Optional[str] = None


# ─── Profile Schemas ──────────────────────────────────────────────

class ProfileAnalysisRequest(BaseModel):
    """Request to analyze an opponent's profile from move history."""
    player_name: str
    pgn_games: list[str]  # List of PGN strings


class ProfileResponse(BaseModel):
    """Opponent profile response."""
    id: UUID
    player_name: str
    style: Optional[str] = None
    aggression_score: float
    risk_tolerance: float
    tactical_preference: float
    positional_preference: float
    endgame_skill: float
    opening_stats: Optional[dict] = None
    psychological_profile: Optional[dict] = None
    total_games_analyzed: int
    avg_centipawn_loss: Optional[float] = None

    class Config:
        from_attributes = True


# ─── WebSocket Schemas ────────────────────────────────────────────

class WSFrameMessage(BaseModel):
    """WebSocket message containing a video frame."""
    type: str = "frame"
    data: str  # base64 encoded image


class WSAnalysisMessage(BaseModel):
    """WebSocket analysis result message."""
    type: str = "analysis"
    fen: str
    evaluation: float
    mate_in: Optional[int] = None
    best_move: Optional[str] = None
    explanation: Optional[str] = None
    threats: list[dict] = []
    heatmap: Optional[list[list[float]]] = None
    processing_time_ms: float
