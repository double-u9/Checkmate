"""WebSocket API — Real-time board analysis from webcam/stream."""

import base64
import time
import json
import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from app.cv.pipeline import CVPipeline
from app.chess_engine.analyzer import ChessAnalyzer
from app.ai.explainer import MoveExplainer

router = APIRouter()

# Maximum base64 payload size: ~5MB base64 ≈ 3.75MB image (P7 fix)
MAX_PAYLOAD_SIZE = 5 * 1024 * 1024  # 5MB in bytes of base64 text


class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Active: {len(self.active_connections)}")

    async def send_json(self, websocket: WebSocket, data: dict):
        await websocket.send_json(data)


manager = ConnectionManager()

# These objects are lightweight now — they use the shared Stockfish singleton
cv_pipeline = CVPipeline()
analyzer = ChessAnalyzer()
explainer = MoveExplainer()


@router.websocket("/live")
async def live_analysis(websocket: WebSocket):
    """Real-time chess analysis from webcam frames."""
    await manager.connect(websocket)
    last_fen = None

    try:
        while True:
            data = await websocket.receive_text()

            # P7: Validate payload size before parsing
            if len(data) > MAX_PAYLOAD_SIZE:
                await manager.send_json(websocket, {
                    "type": "error",
                    "message": f"Payload too large. Maximum: {MAX_PAYLOAD_SIZE // (1024*1024)}MB",
                })
                continue

            try:
                msg = json.loads(data)
            except json.JSONDecodeError:
                await manager.send_json(websocket, {
                    "type": "error",
                    "message": "Invalid JSON payload",
                })
                continue

            if msg.get("type") == "frame":
                start = time.time()

                try:
                    # P7: Validate base64 data field exists and is within size limits
                    frame_data = msg.get("data")
                    if not frame_data or not isinstance(frame_data, str):
                        await manager.send_json(websocket, {
                            "type": "error",
                            "message": "Missing or invalid 'data' field",
                        })
                        continue

                    if len(frame_data) > MAX_PAYLOAD_SIZE:
                        await manager.send_json(websocket, {
                            "type": "error",
                            "message": "Frame data too large",
                        })
                        continue

                    # Decode base64 frame
                    image_data = base64.b64decode(frame_data)
                    nparr = np.frombuffer(image_data, np.uint8)

                    # Run CV pipeline
                    cv_result = await cv_pipeline.process_image(nparr)

                    if cv_result["board_detected"]:
                        current_fen = cv_result["fen"]

                        # Only re-analyze if position changed
                        if current_fen != last_fen:
                            last_fen = current_fen

                            # Run chess analysis
                            analysis = await analyzer.analyze_position(
                                fen=current_fen, depth=15, num_lines=3
                            )

                            elapsed = (time.time() - start) * 1000

                            await manager.send_json(websocket, {
                                "type": "analysis",
                                "fen": current_fen,
                                "evaluation": analysis.evaluation,
                                "mate_in": analysis.mate_in,
                                "best_move": analysis.best_move.move_san,
                                "explanation": analysis.explanation,
                                "threats": [t.model_dump() for t in analysis.threats],
                                "heatmap": analysis.heatmap,
                                "processing_time_ms": round(elapsed, 2),
                            })
                        else:
                            await manager.send_json(websocket, {
                                "type": "no_change",
                                "fen": current_fen,
                            })
                    else:
                        await manager.send_json(websocket, {
                            "type": "no_board",
                            "message": "No chessboard detected in frame",
                        })

                except Exception as e:
                    logger.error(f"Frame processing error: {e}")
                    await manager.send_json(websocket, {
                        "type": "error",
                        "message": str(e),
                    })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
