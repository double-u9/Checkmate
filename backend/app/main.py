"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import sys
import time
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from app.config import get_settings
from app.api.routes import analysis, games, profiles, vision, websocket
from app.db.session import init_db
from app.chess_engine.stockfish import shutdown_engine


# Configure loguru
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="DEBUG" if get_settings().debug else "INFO",
)
logger.add("logs/aethelred.log", rotation="10 MB", retention="7 days", level="DEBUG")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    logger.info("🏰 Aethelred starting up...")
    settings = get_settings()

    # Initialize database
    await init_db()
    logger.info("✅ Database initialized")

    # Log configuration
    logger.info(f"📍 Stockfish path: {settings.stockfish_path}")
    logger.info(f"🔍 CV confidence threshold: {settings.cv_confidence_threshold}")

    yield

    # ─── Shutdown: Clean up all resources ───
    logger.info("🏰 Aethelred shutting down...")

    # Properly close Stockfish engine (P3 fix)
    await shutdown_engine()
    logger.info("✅ Stockfish engine shut down cleanly")


app = FastAPI(
    title="Aethelred",
    description="Vision-Based Chess Strategy Analyzer & Opponent Profiler",
    version="1.0.0",
    lifespan=lifespan,
)


# ─── Rate Limiting Middleware ───────────────────────────────────────
# Simple in-memory rate limiter for production hardening (P6)
_rate_limit_store: dict[str, list[float]] = {}
RATE_LIMIT_REQUESTS = 60  # requests per window
RATE_LIMIT_WINDOW = 60    # window in seconds


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Basic rate limiting middleware. Limits requests per IP per time window."""
    # Skip rate limiting for health checks and WebSocket upgrades
    if request.url.path == "/health" or request.url.path.startswith("/ws"):
        return await call_next(request)
    
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    
    # Clean old entries and check rate
    if client_ip not in _rate_limit_store:
        _rate_limit_store[client_ip] = []
    
    # Remove timestamps outside the current window
    _rate_limit_store[client_ip] = [
        ts for ts in _rate_limit_store[client_ip]
        if now - ts < RATE_LIMIT_WINDOW
    ]
    
    if len(_rate_limit_store[client_ip]) >= RATE_LIMIT_REQUESTS:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Try again later."},
            headers={"Retry-After": str(RATE_LIMIT_WINDOW)},
        )
    
    _rate_limit_store[client_ip].append(now)
    response = await call_next(request)
    return response


# CORS middleware — restricted origins (P6 fix)
settings = get_settings()
allowed_origins = [
    "http://localhost:3000",      # Next.js dev server
    "http://localhost:8000",      # FastAPI dev server
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
]

# In debug mode, also allow wildcard for development convenience
if settings.debug:
    allowed_origins.append("*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Register routers
app.include_router(vision.router, prefix="/api/v1/vision", tags=["Vision"])
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["Analysis"])
app.include_router(games.router, prefix="/api/v1/games", tags=["Games"])
app.include_router(profiles.router, prefix="/api/v1/profiles", tags=["Profiles"])
app.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "aethelred", "version": "1.0.0"}
