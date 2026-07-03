"""Games API — CRUD operations for chess games."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.db.session import get_db
from app.models.database import Game, Position
from app.models.schemas import GameCreate, GameResponse, AddMoveRequest
from app.chess_engine.analyzer import ChessAnalyzer

router = APIRouter()
analyzer = ChessAnalyzer()


@router.post("/", response_model=GameResponse)
async def create_game(game: GameCreate, db: AsyncSession = Depends(get_db)):
    """Create a new game session."""
    db_game = Game(
        white_name=game.white_name,
        black_name=game.black_name,
        source=game.source,
    )
    db.add(db_game)
    await db.flush()
    await db.commit()
    await db.refresh(db_game)

    return GameResponse(
        id=db_game.id,
        white_name=db_game.white_name,
        black_name=db_game.black_name,
        result=db_game.result,
        pgn=db_game.pgn,
        opening_eco=db_game.opening_eco,
        opening_name=db_game.opening_name,
        source=db_game.source,
        created_at=db_game.created_at,
        move_count=0,
    )


@router.get("/{game_id}", response_model=GameResponse)
async def get_game(game_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get game details by ID."""
    result = await db.execute(select(Game).where(Game.id == game_id))
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    positions = await db.execute(
        select(Position).where(Position.game_id == game_id)
    )
    move_count = len(positions.scalars().all())

    return GameResponse(
        id=game.id,
        white_name=game.white_name,
        black_name=game.black_name,
        result=game.result,
        pgn=game.pgn,
        opening_eco=game.opening_eco,
        opening_name=game.opening_name,
        source=game.source,
        created_at=game.created_at,
        move_count=move_count,
    )


@router.put("/{game_id}/moves")
async def add_move(game_id: UUID, move: AddMoveRequest, db: AsyncSession = Depends(get_db)):
    """Add a move to an existing game and get analysis."""
    result = await db.execute(select(Game).where(Game.id == game_id))
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Count existing moves
    positions = await db.execute(
        select(Position).where(Position.game_id == game_id)
    )
    move_number = len(positions.scalars().all()) + 1

    # Analyze the position
    try:
        analysis = await analyzer.analyze_position(fen=move.fen, depth=20, num_lines=3)
    except Exception as e:
        logger.warning(f"Analysis failed for move, storing without: {e}")
        analysis = None

    position = Position(
        game_id=game_id,
        move_number=move_number,
        fen=move.fen,
        move_uci=move.move_uci,
        move_san=move.move_san,
        evaluation=analysis.evaluation if analysis else None,
        best_move=analysis.best_move.move_san if analysis else None,
        explanation=analysis.explanation if analysis else None,
    )
    db.add(position)
    await db.flush()
    await db.commit()

    return {"status": "ok", "move_number": move_number, "analysis": analysis}


@router.get("/{game_id}/pgn")
async def export_pgn(game_id: UUID, db: AsyncSession = Depends(get_db)):
    """Export game as PGN."""
    result = await db.execute(select(Game).where(Game.id == game_id))
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    return {"pgn": game.pgn or "[Event \"Aethelred Analysis\"]\n[Result \"*\"]\n*"}
