"""Vision API — Board detection from images and video."""

import time
import base64
import numpy as np
from fastapi import APIRouter, UploadFile, File, HTTPException
from loguru import logger

from app.models.schemas import BoardDetectionResponse, Base64ImageRequest
from app.cv.pipeline import CVPipeline

router = APIRouter()
cv_pipeline = CVPipeline()

# Maximum upload size: 10MB
MAX_UPLOAD_SIZE = 10 * 1024 * 1024


@router.post("/detect", response_model=BoardDetectionResponse)
async def detect_board(file: UploadFile = File(...)):
    """Detect a chessboard from an uploaded image and return FEN."""
    start = time.time()

    # Validate file type
    if file.content_type not in ["image/png", "image/jpeg", "image/webp", "image/bmp"]:
        raise HTTPException(status_code=400, detail="Unsupported image format. Use PNG, JPEG, WebP, or BMP.")

    try:
        contents = await file.read()

        # Validate file size
        if len(contents) > MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Image too large. Maximum size: {MAX_UPLOAD_SIZE // (1024*1024)}MB"
            )

        nparr = np.frombuffer(contents, np.uint8)

        result = await cv_pipeline.process_image(nparr)
        elapsed = (time.time() - start) * 1000

        return BoardDetectionResponse(
            fen=result["fen"],
            confidence=result["confidence"],
            board_detected=result["board_detected"],
            squares=result.get("squares"),
            processing_time_ms=round(elapsed, 2),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Board detection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


@router.post("/detect-base64", response_model=BoardDetectionResponse)
async def detect_board_base64(request: Base64ImageRequest):
    """Detect board from a base64-encoded image (used by webcam)."""
    start = time.time()

    try:
        image_data = base64.b64decode(request.image)
        nparr = np.frombuffer(image_data, np.uint8)

        result = await cv_pipeline.process_image(nparr)
        elapsed = (time.time() - start) * 1000

        return BoardDetectionResponse(
            fen=result["fen"],
            confidence=result["confidence"],
            board_detected=result["board_detected"],
            squares=result.get("squares"),
            processing_time_ms=round(elapsed, 2),
        )
    except Exception as e:
        logger.error(f"Base64 board detection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")

