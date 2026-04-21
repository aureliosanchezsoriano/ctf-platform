import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.challenge import Challenge
from app.models.attempt import Attempt

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/hints", tags=["hints"])


class HintRevealResponse(BaseModel):
    index: int
    text: str
    cost: int
    points_deducted: int


class HintStatusResponse(BaseModel):
    challenge_slug: str
    revealed: list[int]
    points_spent: int


@router.get("/{slug}", response_model=HintStatusResponse)
async def get_hint_status(
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

    result = await db.execute(
        select(Attempt).where(
            Attempt.user_id == current_user.id,
            Attempt.challenge_id == challenge.id,
            Attempt.submitted_flag.like("hint:%"),
        )
    )
    hint_attempts = result.scalars().all()

    hints = challenge.hints or []
    revealed = []
    points_spent = 0
    for a in hint_attempts:
        index = int(a.submitted_flag.split(":")[1])
        revealed.append(index)
        if index < len(hints):
            points_spent += hints[index]["cost"]

    return HintStatusResponse(
        challenge_slug=slug,
        revealed=revealed,
        points_spent=points_spent,
    )


@router.post("/{slug}/{index}", response_model=HintRevealResponse)
async def reveal_hint(
    slug: str,
    index: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Challenge).where(Challenge.slug == slug, Challenge.is_active == True)
    )
    challenge = result.scalar_one_or_none()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    hints = challenge.hints or []
    if index < 0 or index >= len(hints):
        raise HTTPException(status_code=404, detail="Hint not found")

    hint = hints[index]

    # Check if already revealed
    existing = await db.execute(
        select(Attempt).where(
            Attempt.user_id == current_user.id,
            Attempt.challenge_id == challenge.id,
            Attempt.submitted_flag == f"hint:{index}",
        )
    )
    if existing.scalar_one_or_none():
        return HintRevealResponse(
            index=index,
            text=hint["text"],
            cost=hint["cost"],
            points_deducted=0,
        )

    attempt = Attempt(
        user_id=current_user.id,
        challenge_id=challenge.id,
        submitted_flag=f"hint:{index}",
        is_correct=False,
    )
    db.add(attempt)
    await db.flush()

    logger.info(f"Hint revealed: user={current_user.username} challenge={slug} hint={index} cost={hint['cost']}")

    return HintRevealResponse(
        index=index,
        text=hint["text"],
        cost=hint["cost"],
        points_deducted=hint["cost"],
    )
