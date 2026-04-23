import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from app.core.database import get_db
from app.core.redis import get_redis
from app.core.auth import get_current_user, get_current_teacher
from app.core.security import generate_flag, verify_flag
from app.core.limiter import check_rate_limit
from app.models.user import User
from app.models.challenge import Challenge
from app.models.attempt import Attempt
from redis.asyncio import Redis

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/challenges", tags=["challenges"])

# Rate limit: 10 submissions per challenge per user per 60 seconds
FLAG_RATE_LIMIT = 10
FLAG_RATE_WINDOW = 60


# ── Schemas ───────────────────────────────────────────────────────────────────

class ChallengeResponse(BaseModel):
    id: str
    slug: str
    name: str
    description: str
    type: str
    category: str
    difficulty: str
    owasp_ref: str | None
    points: int
    is_required: bool
    flag_type: str
    hints: list[dict]
    unlocks_after: str | None
    solved: bool = False
    attempts_count: int = 0
    locked: bool = False

    model_config = {"from_attributes": True}


class FlagSubmission(BaseModel):
    flag: str


class FlagResult(BaseModel):
    correct: bool
    message: str
    points_earned: int = 0


# ── Helpers ───────────────────────────────────────────────────────────────────

async def get_solved_slugs(user_id, db: AsyncSession) -> set[str]:
    result = await db.execute(
        select(Challenge.slug)
        .join(Attempt, Attempt.challenge_id == Challenge.id)
        .where(Attempt.user_id == user_id, Attempt.is_correct == True)
    )
    return {row[0] for row in result.fetchall()}


async def build_response(
    challenge: Challenge,
    solved_slugs: set[str],
    attempt_counts: dict[str, int],
) -> ChallengeResponse:
    solved = challenge.slug in solved_slugs
    locked = bool(
        challenge.unlocks_after
        and challenge.unlocks_after not in solved_slugs
    )
    hints = [{"index": i, "cost": h["cost"], "text": h["text"]}
             for i, h in enumerate(challenge.hints or [])]

    return ChallengeResponse(
        id=str(challenge.id),
        slug=challenge.slug,
        name=challenge.name,
        description=challenge.description,
        type=challenge.type,
        category=challenge.category,
        difficulty=challenge.difficulty,
        owasp_ref=challenge.owasp_ref,
        points=challenge.points,
        is_required=challenge.is_required,
        flag_type=challenge.flag_type,
        hints=hints,
        unlocks_after=challenge.unlocks_after,
        solved=solved,
        attempts_count=attempt_counts.get(challenge.slug, 0),
        locked=locked,
    )


# ── Student routes ────────────────────────────────────────────────────────────

@router.get("", response_model=list[ChallengeResponse])
async def list_challenges(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Challenge)
        .where(Challenge.is_active == True)
        .order_by(Challenge.points.asc())
    )
    challenges = result.scalars().all()

    solved_slugs = await get_solved_slugs(current_user.id, db)

    counts_result = await db.execute(
        select(Challenge.slug, func.count(Attempt.id))
        .join(Attempt, Attempt.challenge_id == Challenge.id)
        .where(Attempt.user_id == current_user.id)
        .group_by(Challenge.slug)
    )
    attempt_counts = {row[0]: row[1] for row in counts_result.fetchall()}

    return [
        await build_response(c, solved_slugs, attempt_counts)
        for c in challenges
    ]


@router.get("/{slug}", response_model=ChallengeResponse)
async def get_challenge(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Challenge).where(Challenge.slug == slug, Challenge.is_active == True)
    )
    challenge = result.scalar_one_or_none()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    solved_slugs = await get_solved_slugs(current_user.id, db)

    # Count attempts for this specific challenge
    count_result = await db.execute(
        select(func.count(Attempt.id)).where(
            Attempt.user_id == current_user.id,
            Attempt.challenge_id == challenge.id,
        )
    )
    count = count_result.scalar() or 0

    return await build_response(challenge, solved_slugs, {challenge.slug: count})


@router.post("/{slug}/submit", response_model=FlagResult)
async def submit_flag(
    slug: str,
    payload: FlagSubmission,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    # Rate limit check — before any DB query
    rate_key = f"flag_submit:{current_user.id}:{slug}"
    await check_rate_limit(redis, rate_key, FLAG_RATE_LIMIT, FLAG_RATE_WINDOW)

    result = await db.execute(
        select(Challenge).where(Challenge.slug == slug, Challenge.is_active == True)
    )
    challenge = result.scalar_one_or_none()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    # Check if already solved
    already = await db.execute(
        select(Attempt).where(
            Attempt.user_id == current_user.id,
            Attempt.challenge_id == challenge.id,
            Attempt.is_correct == True,
        )
    )
    if already.scalar_one_or_none():
        return FlagResult(correct=True, message="Already solved", points_earned=0)

    # Validate the flag
    if challenge.flag_type == "dynamic":
        correct = verify_flag(payload.flag, str(current_user.id), challenge.slug)
    else:
        correct = payload.flag.strip() == (challenge.flag_value or "").strip()

    # Record attempt
    attempt = Attempt(
        user_id=current_user.id,
        challenge_id=challenge.id,
        submitted_flag=payload.flag,
        is_correct=correct,
    )
    db.add(attempt)
    await db.flush()

    if correct:
        logger.info(f"Flag correct: user={current_user.username} challenge={slug}")
        return FlagResult(correct=True, message="Correct! Flag accepted.", points_earned=challenge.points)

    logger.info(f"Flag wrong: user={current_user.username} challenge={slug}")
    return FlagResult(correct=False, message="Incorrect flag, try again.")


# ── Teacher routes ────────────────────────────────────────────────────────────

@router.patch("/{slug}/activate", dependencies=[Depends(get_current_teacher)])
async def activate_challenge(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Challenge).where(Challenge.slug == slug))
    challenge = result.scalar_one_or_none()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    challenge.is_active = True
    return {"slug": slug, "is_active": True}


@router.patch("/{slug}/deactivate", dependencies=[Depends(get_current_teacher)])
async def deactivate_challenge(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Challenge).where(Challenge.slug == slug))
    challenge = result.scalar_one_or_none()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    challenge.is_active = False
    return {"slug": slug, "is_active": False}


# ── Container management ──────────────────────────────────────────────────────

class ContainerInfo(BaseModel):
    running: bool
    url: str | None = None
    container_id: str | None = None
    status: str


@router.post("/{slug}/start", response_model=ContainerInfo)
async def start_challenge_container(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.orchestrator import start_challenge, get_docker_client
    import docker.errors

    result = await db.execute(
        select(Challenge).where(Challenge.slug == slug, Challenge.is_active == True)
    )
    challenge = result.scalar_one_or_none()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    if challenge.type != "docker":
        raise HTTPException(status_code=400, detail="This challenge does not use a container")

    try:
        info = start_challenge(
            user_id=str(current_user.id),
            challenge_slug=slug,
            docker_config=challenge.docker_config,
        )
        return ContainerInfo(
            running=True,
            url=info["url"],
            container_id=info["container_id"],
            status=info["status"],
        )
    except Exception as e:
        logger.error(f"Failed to start container: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start container: {str(e)}")


@router.delete("/{slug}/stop", response_model=ContainerInfo)
async def stop_challenge_container(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.orchestrator import stop_challenge

    result = await db.execute(
        select(Challenge).where(Challenge.slug == slug)
    )
    challenge = result.scalar_one_or_none()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    stopped = stop_challenge(str(current_user.id), slug)
    return ContainerInfo(
        running=False,
        status="stopped" if stopped else "not_found",
    )


@router.get("/{slug}/status", response_model=ContainerInfo)
async def challenge_container_status(
    slug: str,
    current_user: User = Depends(get_current_user),
):
    from app.services.orchestrator import get_container_status

    info = get_container_status(str(current_user.id), slug)
    return ContainerInfo(
        running=info["running"],
        url=info.get("url"),
        container_id=info.get("container_id"),
        status=info["status"],
    )


# ── File download ─────────────────────────────────────────────────────────────

from fastapi.responses import FileResponse
from pathlib import Path

CHALLENGES_DIR = Path(__file__).resolve().parents[3] / "challenges"


@router.get("/{slug}/files")
async def download_challenge_files(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Challenge).where(Challenge.slug == slug, Challenge.is_active == True)
    )
    challenge = result.scalar_one_or_none()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    if challenge.type != "file":
        raise HTTPException(status_code=400, detail="This challenge does not have files")

    file_config = challenge.file_config or {}
    filename = file_config.get("filename", "challenge.zip")
    files_path = CHALLENGES_DIR / slug / file_config.get("path", "files/").rstrip("/")
    target = files_path / filename

    if not target.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")

    return FileResponse(
        path=str(target),
        filename=target.name,
        media_type="application/octet-stream",
    )
