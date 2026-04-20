import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from app.core.database import get_db
from app.core.auth import get_current_user, get_current_teacher
from app.core.security import generate_flag, verify_flag
from app.models.user import User
from app.models.challenge import Challenge, ChallengeType
from app.models.attempt import Attempt

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/challenges", tags=["challenges"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class HintResponse(BaseModel):
    index: int
    cost: int
    text: str


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
    locked: bool = False    # True if prerequisite not met

    model_config = {"from_attributes": True}


class FlagSubmission(BaseModel):
    flag: str


class FlagResult(BaseModel):
    correct: bool
    message: str
    points_earned: int = 0


# ── Helpers ───────────────────────────────────────────────────────────────────

async def get_solved_slugs(user_id: UUID, db: AsyncSession) -> set[str]:
    """Return the set of challenge slugs solved by this user."""
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
    # Hide hint text for locked hints (cost > 0) unless already solved
    hints = []
    for i, h in enumerate(challenge.hints or []):
        hints.append({"index": i, "cost": h["cost"], "text": h["text"]})

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
    """Return all active challenges with solved/locked status for the current user."""
    result = await db.execute(
        select(Challenge)
        .where(Challenge.is_active == True)
        .order_by(Challenge.points.asc())
    )
    challenges = result.scalars().all()

    solved_slugs = await get_solved_slugs(current_user.id, db)

    # Count attempts per challenge for this user in one query
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
    return await build_response(challenge, solved_slugs, {})


@router.post("/{slug}/submit", response_model=FlagResult)
async def submit_flag(
    slug: str,
    payload: FlagSubmission,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
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

    # Record the attempt
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
        return FlagResult(
            correct=True,
            message="Correct! Flag accepted.",
            points_earned=challenge.points,
        )
    else:
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
