"""Profiles API — Opponent profiling and analysis."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.db.session import get_db
from app.models.database import Profile
from app.models.schemas import ProfileAnalysisRequest, ProfileResponse
from app.ai.opponent_profiler import OpponentProfiler

router = APIRouter()
profiler = OpponentProfiler()


@router.post("/analyze", response_model=ProfileResponse)
async def analyze_opponent(request: ProfileAnalysisRequest, db: AsyncSession = Depends(get_db)):
    """Analyze an opponent's playing style from PGN games."""
    try:
        profile_data = await profiler.analyze(
            player_name=request.player_name,
            pgn_games=request.pgn_games,
        )

        # Upsert profile in database
        result = await db.execute(
            select(Profile).where(Profile.player_name == request.player_name)
        )
        existing = result.scalar_one_or_none()

        if existing:
            for key, value in profile_data.items():
                setattr(existing, key, value)
            existing.total_games_analyzed += len(request.pgn_games)
            await db.flush()
            await db.commit()
            await db.refresh(existing)
            profile = existing
        else:
            profile = Profile(
                player_name=request.player_name,
                total_games_analyzed=len(request.pgn_games),
                **profile_data,
            )
            db.add(profile)
            await db.flush()
            await db.commit()
            await db.refresh(profile)

        return ProfileResponse.model_validate(profile)
    except Exception as e:
        logger.error(f"Profile analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Profiling failed: {str(e)}")


@router.get("/{profile_id}", response_model=ProfileResponse)
async def get_profile(profile_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get an opponent profile by ID."""
    result = await db.execute(select(Profile).where(Profile.id == profile_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return ProfileResponse.model_validate(profile)
