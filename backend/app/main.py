import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.services.challenge_loader import sync_challenges
from app.routers import auth, challenges, scoreboard, hints, admin

logger = logging.getLogger(__name__)
settings = get_settings()

CHALLENGES_DIR = Path(__file__).resolve().parents[2] / "challenges"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Scanning challenges at: {CHALLENGES_DIR}")
    if CHALLENGES_DIR.exists():
        async with AsyncSessionLocal() as db:
            count = await sync_challenges(db, CHALLENGES_DIR)
            logger.info(f"Synced {count} challenges from disk")
    else:
        logger.warning(f"Challenges directory not found: {CHALLENGES_DIR}")
    yield


app = FastAPI(
    title="CTF Platform",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(challenges.router)
app.include_router(scoreboard.router)
app.include_router(hints.router)
app.include_router(admin.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "environment": settings.environment}
