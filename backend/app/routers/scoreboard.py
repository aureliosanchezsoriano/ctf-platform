from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from pydantic import BaseModel
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User, UserRole
from app.models.challenge import Challenge
from app.models.attempt import Attempt

router = APIRouter(prefix="/api/scoreboard", tags=["scoreboard"])


class ScoreboardEntry(BaseModel):
    rank: int
    username: str
    full_name: str
    class_name: str | None
    points: int
    solved_count: int
    last_solve: str | None


@router.get("", response_model=list[ScoreboardEntry])
async def get_scoreboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # One query: per student, sum points of correct attempts and count solves
    # Join challenges to get points, filter only students
    result = await db.execute(
        select(
            User.username,
            User.full_name,
            User.class_name,
            func.coalesce(func.sum(Challenge.points), 0).label("points"),
            func.count(Attempt.id).label("solved_count"),
            func.max(Attempt.attempted_at).label("last_solve"),
        )
        .outerjoin(
            Attempt,
            (Attempt.user_id == User.id) & (Attempt.is_correct == True),
        )
        .outerjoin(Challenge, Challenge.id == Attempt.challenge_id)
        .where(User.role == UserRole.student, User.is_active == True)
        .group_by(User.username, User.full_name, User.class_name)
        .order_by(
            text("points DESC"),
            text("last_solve ASC NULLS LAST"),
        )
    )
    rows = result.fetchall()

    return [
        ScoreboardEntry(
            rank=i + 1,
            username=row.username,
            full_name=row.full_name,
            class_name=row.class_name,
            points=row.points,
            solved_count=row.solved_count,
            last_solve=row.last_solve.isoformat() if row.last_solve else None,
        )
        for i, row in enumerate(rows)
    ]
