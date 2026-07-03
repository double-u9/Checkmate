"""Analysis API — Chess position analysis and move explanations."""

from fastapi import APIRouter, HTTPException
from loguru import logger

from app.models.schemas import (
    PositionAnalysisRequest,
    AnalysisResponse,
    ExplanationRequest,
    ExplanationResponse,
)
from app.chess_engine.analyzer import ChessAnalyzer
from app.ai.explainer import MoveExplainer

router = APIRouter()
analyzer = ChessAnalyzer()
explainer = MoveExplainer()


@router.post("/position", response_model=AnalysisResponse)
async def analyze_position(request: PositionAnalysisRequest):
    """Analyze a chess position given a FEN string."""
    try:
        result = await analyzer.analyze_position(
            fen=request.fen,
            depth=request.depth,
            num_lines=request.num_lines,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Position analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/explain", response_model=ExplanationResponse)
async def explain_move(request: ExplanationRequest):
    """Get a human-readable explanation of why a move is good or bad."""
    try:
        result = await explainer.explain_move(
            fen=request.fen,
            move_uci=request.move_uci,
            depth=request.depth,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Move explanation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Explanation failed: {str(e)}")
